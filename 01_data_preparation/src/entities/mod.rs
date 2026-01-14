use serde::Deserialize;

#[derive(Deserialize, Debug)]
pub struct EnaRun {
    pub study_accession: String,
    pub run_accession: String,
    pub fastq_ftp: Option<String>,
    pub fastq_bytes: Option<String>,
}