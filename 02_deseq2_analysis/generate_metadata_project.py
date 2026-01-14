import pandas as pd
import requests
from io import BytesIO
import xml.etree.ElementTree as ET

def generate_metadata_project(project_acc="PRJEB79238", output_csv="metadata_project.csv"):
    """
    Genera un CSV con todos los metadatos de un proyecto ENA completo.
    Incluye: sample_accession, run_accession, experiment_accession, tax_id,
    scientific_name, instrument, library info, fastq files, y atributos de muestra.
    """
    
    # --- 1. Obtener la lista de samples del proyecto ---
    samples_url = f"https://www.ebi.ac.uk/ena/browser/api/xml/{project_acc}?download=true"
    r = requests.get(samples_url)
    r.raise_for_status()
    project_xml = ET.parse(BytesIO(r.content))
    
    # Extraer todas las SAMPLE_ACCESSION
    sample_acc_list = [s.attrib["accession"] for s in project_xml.findall(".//SAMPLE")]
    
    all_samples = []
    all_runs = []
    
    # --- 2. Iterar por cada sample ---
    for sample_acc in sample_acc_list:
        # Descargar XML de la muestra
        sample_tree = ET.parse(BytesIO(requests.get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{sample_acc}").content))
        sample_elem = sample_tree.find(".//SAMPLE")
        
        sample_dict = {
            "sample_accession": sample_elem.attrib.get("accession"),
            "alias": sample_elem.attrib.get("alias"),
            "title": sample_elem.findtext("TITLE")
        }
        
        # Tax info
        sn = sample_elem.find("SAMPLE_NAME")
        if sn is not None:
            sample_dict["tax_id"] = sn.findtext("TAXON_ID")
            sample_dict["scientific_name"] = sn.findtext("SCIENTIFIC_NAME")
        
        # SAMPLE_ATTRIBUTES
        for attr in sample_elem.findall(".//SAMPLE_ATTRIBUTE"):
            tag = attr.findtext("TAG")
            value = attr.findtext("VALUE")
            units = attr.findtext("UNITS")
            colname = tag.lower().replace(" ", "_")
            if units:
                value = f"{value} {units}"
            sample_dict[colname] = value
            
        all_samples.append(sample_dict)
        
        # --- 3. Obtener experimentos asociados a esta sample ---
        exp_links = sample_elem.findall(".//SAMPLE_LINK/XREF_LINK/ID")
        for exp_link in exp_links:
            # Si es ENA-FASTQ-FILES obtenemos los runs
            if "filereport" in exp_link.text:
                runs_url = exp_link.text.strip()
                df_runs = pd.read_csv(runs_url, sep="\t")
                
                # Añadir sample info a cada run
                df_runs["sample_accession"] = sample_dict["sample_accession"]
                df_runs["alias"] = sample_dict["alias"]
                df_runs["title"] = sample_dict["title"]
                df_runs["tax_id"] = sample_dict.get("tax_id")
                df_runs["scientific_name"] = sample_dict.get("scientific_name")
                
                # Añadir atributos de sample
                for key in sample_dict.keys():
                    if key not in df_runs.columns:
                        df_runs[key] = sample_dict[key]
                
                all_runs.append(df_runs)
    
    # --- 4. Combinar todos los runs en un solo DataFrame ---
    if all_runs:
        metadata_df = pd.concat(all_runs, ignore_index=True)
        metadata_df.to_csv(output_csv, index=False)
        print(f"Tabla de metadatos creada: {output_csv}")
        return metadata_df
    else:
        print("No se encontraron runs para este proyecto.")
        return None


# --- USO ---
df = generate_metadata_project("PRJEB79238", "metadata_PRJEB79238.csv")
