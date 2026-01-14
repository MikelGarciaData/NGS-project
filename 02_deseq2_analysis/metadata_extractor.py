import xml.etree.ElementTree as ET
import pandas as pd
import requests
from io import BytesIO

# --- 1. Definir las accesiones ---
sample_acc = "SAMEA115940987"
experiment_acc = "ERX12946888"
run_acc = "ERR13576985"
taxon_acc = "410658"

params = {"sample_acc": "SAMEA115940987", 
            "experiment_acc": "ERX12946888", 
            "run_acc": "ERR13576985",
            "taxon_acc": "410658"
}

def metadata_extractor(sample_acc, experiment_acc, run_acc, taxon_acc):
    """
    Descarga los XML de ENA y extrae los metadatos de una sola muestra/run.
    Devuelve una lista con los valores en el mismo orden que cols_order.
    """
    import requests
    import xml.etree.ElementTree as ET
    from io import BytesIO

    # --- Inicializar diccionario de metadata ---
    metadata = {}

    # --- Sample XML ---
    sample_tree = ET.parse(BytesIO(requests.get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{sample_acc}").content))
    sample_elem = sample_tree.find(".//SAMPLE")

    metadata['sample_accession'] = sample_elem.attrib.get("accession")
    metadata['alias'] = sample_elem.attrib.get("alias")
    metadata['title'] = sample_elem.findtext("TITLE")

    # Tax info
    sn = sample_elem.find("SAMPLE_NAME")
    if sn is not None:
        metadata['tax_id'] = sn.findtext("TAXON_ID")
        metadata['scientific_name'] = sn.findtext("SCIENTIFIC_NAME")

    # Sample attributes
    for attr in sample_elem.findall(".//SAMPLE_ATTRIBUTE"):
        tag = attr.findtext("TAG").lower().replace(" ", "_")
        value = attr.findtext("VALUE")
        units = attr.findtext("UNITS")
        if units:
            value = f"{value} {units}"
        metadata[tag] = value

    # --- Experiment XML ---
    exp_tree = ET.parse(BytesIO(requests.get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{experiment_acc}").content))
    exp_elem = exp_tree.find(".//EXPERIMENT")
    if exp_elem is not None:
        metadata['library_strategy'] = exp_elem.findtext(".//LIBRARY_STRATEGY")
        metadata['library_layout'] = "paired" if exp_elem.find(".//PAIRED") is not None else "single"
        metadata['instrument_model'] = exp_elem.findtext(".//INSTRUMENT_MODEL")

    # --- Run XML ---
    run_tree = ET.parse(BytesIO(requests.get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{run_acc}").content))
    run_elem = run_tree.find(".//RUN")
    if run_elem is not None:
        fastq_files = run_elem.findall(".//FILES/FILE[@filetype='fastq']")
        for i, f in enumerate(fastq_files):
            metadata[f"fastq_{i+1}"] = f.attrib.get("filename")

    # --- Taxon XML ---
    taxon_tree = ET.parse(BytesIO(requests.get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{taxon_acc}").content))
    taxon_elem = taxon_tree.find(".//taxon")
    if taxon_elem is not None:
        metadata['taxon_scientific_name'] = taxon_elem.attrib.get("scientificName")
        metadata['taxon_id'] = taxon_elem.attrib.get("taxId")
        metadata['rank'] = taxon_elem.attrib.get("rank")

    # --- Orden de columnas deseadas ---
    cols_order = ["sample_accession", "alias", "run_accession", "experiment_accession",
                  "library_strategy", "library_layout", "instrument_model",
                  "tax_id", "scientific_name", "title", "fastq_1", "fastq_2",
                  "collection_date", "geographic_location_(longitude)", "geographic_location_(latitude)",
                  "depth", "elevation", "environmental_medium", "local_environmental_context", "project_name",
                  "broad-scale_environmental_context", "description"]

    # Completar fastq y run/experiment info
    metadata['run_accession'] = run_acc
    metadata['experiment_accession'] = experiment_acc

    # Convertir a lista en el orden deseado (valores vacíos si no existen)
    return [metadata.get(col, "") for col in cols_order]

