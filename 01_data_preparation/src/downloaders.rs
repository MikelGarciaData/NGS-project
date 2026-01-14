use reqwest::blocking::Client;
use std::fs::{self, OpenOptions, File};
use std::io::{self, Write, copy};
use regex::Regex;
use crate::entities::EnaRun;
use indicatif::{ProgressBar, ProgressStyle};

pub fn download_metagenomics_data(search_term: &str, client: &Client) -> Result<(), Box<dyn std::error::Error>> {
    let project_regex = Regex::new(r"^(PRJ[E|N|A][A-Z0-9]+)$")?;
    let is_project = project_regex.is_match(search_term.trim());

    let clean_term = search_term.replace("\"", "");

    let (folder_path, query) = if is_project {
        (format!("data/{}", clean_term), format!("study_accession={}", clean_term))
    } else {
        let clean_name = clean_term.to_lowercase().replace(|c: char| !c.is_alphanumeric(), "_");
        let folder = format!("data/palabras_claves/{}", clean_name);
        
        // Lógica inteligente para múltiples términos (AND)
        let q = if clean_term.contains(" AND ") {
            let parts: Vec<&str> = clean_term.split(" AND ").collect();
            let sub_queries: Vec<String> = parts.iter()
                .map(|p| format!("(study_title=\"*{p}*\" OR description=\"*{p}*\")"))
                .collect();
            sub_queries.join(" AND ")
        } else {
            format!("(study_title=\"*{clean_term}*\" OR description=\"*{clean_term}*\")")
        };

        (folder, q)
    };

    let url = "https://www.ebi.ac.uk/ena/portal/api/search";
    
    // Parámetros optimizados para ENA
    let params = [
        ("result", "read_run"),
        ("query", &query),
        ("fields", "study_accession,run_accession,fastq_ftp,fastq_bytes"),
        ("format", "json"),
        ("include_metagenomes", "true"), // Crucial para proyectos como EMBARQ
    ];

    let response = client.get(url).query(&params).send()?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response.text().unwrap_or_default();
        eprintln!("[-] Error {} para: {}. Detalle: {}", status, search_term, error_text);
        return Ok(());
    }

    // Parseo de seguridad
    let text = response.text()?;
    if text.trim().is_empty() || text == "{}" {
        println!("[-] Sin resultados para: {}", search_term);
        return Ok(());
    }

    let results: Vec<EnaRun> = serde_json::from_str(&text).map_err(|e| {
        format!("Error al parsear JSON: {}. Texto recibido: {}", e, text)
    })?;

    // ... (El resto de la lógica de bytes y guardado se mantiene igual)
    process_and_save(results, search_term, &folder_path, is_project, client)?;

    Ok(())
}

fn process_and_save(results: Vec<EnaRun>, search_term: &str, folder_path: &str, is_project: bool, client: &Client) -> io::Result<()> {
    let mut total_bytes: u64 = 0;

    // --- Mostrar Tabla de Archivos ---
    println!("\n{:<20} | {:<15} | {:<10}", "Run Accession", "Estudio", "Tamaño (GB)");
    println!("{}", "-".repeat(50));

    // Mostramos los primeros 10 para no saturar la terminal
    for (i, run) in results.iter().enumerate() {
        let mut run_bytes: u64 = 0;
        if let Some(bytes_str) = &run.fastq_bytes {
            for b in bytes_str.split(';') {
                if let Ok(b_val) = b.parse::<u64>() {
                    run_bytes += b_val;
                    total_bytes += b_val;
                }
            }
        }

        if i < 10 {
            let gb = run_bytes as f64 / 1024.0_f64.powi(3);
            println!("{:<20} | {:<15} | {:.4} GB", 
                run.run_accession, 
                run.study_accession, 
                gb
            );
        } else if i == 10 {
            println!("... y {} archivos más.", results.len() - 10);
        }
    }

    let total_gb = total_bytes as f64 / 1024.0_f64.powi(3);
    println!("{}", "-".repeat(50));
    println!("RESUMEN FINAL:");
    println!("BÚSQUEDA: {}", search_term);
    println!("Total de archivos: {}", results.len());
    println!("Peso Total: {:.2} GB", total_gb);
    println!("{}", "=".repeat(50));

    // --- Confirmación y Guardado ---
    print!("¿Confirmar guardado de metadatos en CSV? (y/n): ");
    io::stdout().flush()?;
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    if input.trim().to_lowercase() == "y" {
        fs::create_dir_all(folder_path)?;
        let mut file = fs::File::create(format!("{}/metadata_runs.csv", folder_path))?;
        writeln!(file, "study_accession,run_accession,fastq_ftp,fastq_bytes")?;
        
        for run in &results {
            writeln!(file, "{},{},{},{}", 
                run.study_accession, 
                run.run_accession, 
                run.fastq_ftp.as_deref().unwrap_or(""), 
                run.fastq_bytes.as_deref().unwrap_or("")
            )?;
        }

        if !is_project {
            let mut indice = OpenOptions::new()
                .create(true)
                .append(true)
                .open("data/palabras_claves/indice_busquedas.txt")?;
            writeln!(indice, "{}: {}", folder_path, search_term)?;
        }
        println!("[+] Metadatos exportados correctamente.");

        print!("¿Deseas descargar los archivos .fastq.gz reales ahora? (y/n): ");
        io::stdout().flush()?;
        let mut download_confirm = String::new();
        io::stdin().read_line(&mut download_confirm)?;

        if download_confirm.trim().to_lowercase() == "y" {
    let total_files = results.iter()
        .filter_map(|r| r.fastq_ftp.as_ref())
        .map(|f| f.split(';').count())
        .sum::<usize>();

    // Creamos la barra de progreso
    let pb = ProgressBar::new(total_files as u64);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .expect("Error en la plantilla de la barra de progreso") // Cambiado ? por expect
        .progress_chars("#>-"));

    for run in &results {
        if let Some(ftp_links) = &run.fastq_ftp {
            for link in ftp_links.split(';') {
                let file_name = link.split('/').last().unwrap_or("archivo.fastq.gz");
                let dest_path = format!("{}/{}", folder_path, file_name);
                
                // Actualizamos el mensaje de la barra con el nombre del archivo actual
                pb.set_message(format!("Descargando {}", file_name));

                // Si quieres saltar archivos que ya existen (muy recomendado):
                if std::path::Path::new(&dest_path).exists() {
                    pb.println(format!("[!] Saltando {}, ya existe.", file_name));
                    pb.inc(1);
                    continue;
                }

                if let Err(e) = download_file_physically(&format!("https://{}", link), &dest_path, client) {
                    pb.println(format!("[!] Error en {}: {}", file_name, e));
                }
                
                pb.inc(1); // Incrementa la barra
            }
        }
    }
    pb.finish_with_message("Descarga completada");
}
    }
    
    Ok(())
}


fn download_file_physically(url: &str, dest: &str, client: &reqwest::blocking::Client) -> Result<(), Box<dyn std::error::Error>> {
    let mut response = client.get(url).send()?;
    if response.status().is_success() {
        let mut file = File::create(dest)?;
        copy(&mut response, &mut file)?;
        println!("[OK] Finalizado: {}", dest);
    } else {
        return Err(format!("Error HTTP: {}", response.status()).into());
    }
    Ok(())
}

// He extraído esta parte para que el código sea más limpio
/*fn process_results(folder_path: &str, search_term: &str, results: Vec<EnaRun>) -> io::Result<()> {
    let mut total_bytes: u64 = 0;
    for run in &results {
        if let Some(bytes_str) = &run.fastq_bytes {
            for b in bytes_str.split(';') {
                if let Ok(b_val) = b.parse::<u64>() {
                    total_bytes += b_val;
                }
            }
        }
    }

    let total_gb = total_bytes as f64 / 1024.0_f64.powi(3);
    println!("\nBÚSQUEDA: {} | Tamaño: {:.2} GB", search_term, total_gb);

    print!("¿Confirmar descarga de metadatos? (y/n): ");
    io::stdout().flush()?;
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    if input.trim().to_lowercase() == "y" {
        fs::create_dir_all(folder_path)?;
        // ... (lógica de escritura de archivos que ya tenías)
        println!("[+] Datos guardados en {}", folder_path);
    }
    Ok(())
}*/


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_regex_project_id() {
        let project_regex = Regex::new(r"^(PRJ[E|N|A][A-Z0-9]+)$").unwrap();
        
        // Casos que deberían ser ciertos
        assert!(project_regex.is_match("PRJEB1787"));
        assert!(project_regex.is_match("PRJNA630132"));
        
        // Casos que NO son IDs de proyecto
        assert!(!project_regex.is_match("Bioinoculants"));
    }

    #[test]
    fn test_folder_naming() {
        let search_term = "\"Soil Metagenome\"";
        let clean_name = search_term.to_lowercase().replace(|c: char| !c.is_alphanumeric(), "_");
        
        // Comprobamos que limpia bien los caracteres raros para la carpeta
        assert_eq!(clean_name, "_soil_metagenome_");
    }
}