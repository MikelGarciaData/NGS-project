## Data preparation

### Rust downloader

Use the data_downloader.rs at src folder for downloading the project data from ENA.

### Nexflow files

01_trimmomatic.nf: Performs sliding window trimming on the fastq files
krakenflow.nf: Runs kraken to obtain a tsv file with counts and another with taxa

## Analysis over gene counts


### Metadata extractor

Each fastq file belongs to an experiment. The experiments have some metadata on the conditions in which the sample was sequence. To see if there's any difference between the different scenarios a CSV with the metadata is created using Python.

### Model
