import pandas as pd

def extract_simple_metadata(project_acc="PRJEB79238", output_csv="metadata_simple.csv"):
    """
    Extrae solo las columnas principales de un proyecto ENA:
    Study Accession, Sample Accession, Experiment Accession, Run Accession, Tax Id
    """
    # URL del filereport ENA
    url = (
        f"https://www.ebi.ac.uk/ena/portal/api/filereport?"
        f"accession={project_acc}&result=read_run&fields=study_accession,sample_accession,experiment_accession,run_accession,tax_id"
    )
    
    # Leer directamente en un DataFrame
    df = pd.read_csv(url, sep="\t")
    
    # Guardar CSV
    df.to_csv(output_csv, index=False)
    print(f"Tabla simple creada: {output_csv}")
    return df

# --- USO ---
df_simple = extract_simple_metadata("PRJEB79238", "metadata_simple_PRJEB79238.csv")
print(df_simple)
