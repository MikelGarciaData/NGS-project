mod entities;      // Declara el módulo de la carpeta models
mod downloaders;  // Declara el módulo del archivo downloader.rs

use reqwest::blocking::Client;

fn main() {
    let client = Client::new();
    let intereses = vec![
        //"PRJEB1787",
        //"PRJNA1158533", 
        //"SRP553560",
        "PRJEB79238",
        //"Bioinoculants AND Soil Metagenome", // Más limpio así
        //"Horizontal Gene Transfer AND Metagenomics",
        //"Microbial Risk Assessment",
        //"soil bioinoculants",
        //"bioremediation",
        //"soil metagenome bioinoculants bioremediation",
        //"Soil Metagenome",
        //"Pesticide degradation",
        //"Bioinoculants AND Soil Metagenome" //should be on a test
    ];

    for item in intereses {
        // Llamamos a la función desde el módulo downloaders
        if let Err(e) = downloaders::download_metagenomics_data(item, &client) {
            eprintln!("Error: {}", e);
        }
    }
}
