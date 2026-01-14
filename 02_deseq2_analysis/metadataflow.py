from metadata_extractor import metadata_extractor
from extract_simple_metadata import extract_simple_metadata
import pandas as pd

# extract_simple_metadata(project_acc="PRJEB79238", output_csv="metadata_simple.csv")
def transform_table_to_csv(df_table, output_csv="metadata_full.csv"):
    """
    Toma un DataFrame simple con columnas:
    study_accession, sample_accession, experiment_accession, run_accession, tax_id
    y genera un CSV con todos los metadatos de ENA.
    """
    all_rows = []
    for _, row in df_table.iterrows():
        try:
            row_metadata = metadata_extractor(
                row['sample_accession'],
                row['experiment_accession'],
                row['run_accession'],
                str(row['tax_id'])
            )
            all_rows.append(row_metadata)
            print(f"Procesada: {row['run_accession']}")
        except Exception as e:
            print(f"Error en {row['run_accession']}: {e}")

    # Crear DataFrame final
    cols_order = ["sample_accession", "alias", "run_accession", "experiment_accession",
                  "library_strategy", "library_layout", "instrument_model",
                  "tax_id", "scientific_name", "title", "fastq_1", "fastq_2",
                  "collection_date", "geographic_location_(longitude)", "geographic_location_(latitude)",
                  "depth", "elevation", "environmental_medium", "local_environmental_context", "project_name",
                  "broad-scale_environmental_context", "description"]
    
    metadata_df = pd.DataFrame(all_rows, columns=cols_order)
    metadata_df.to_csv(output_csv, index=False)
    print(f"Archivo final guardado: {output_csv}")
    return metadata_df

df = pd.read_csv("metadata_simple_PRJEB79238.csv")
transform_table_to_csv(df)