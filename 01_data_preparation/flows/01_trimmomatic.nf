nextflow.enable.dsl=2

// run with: nextflow run flows/01_trimmomatic.nf -c flows/trimmomatic.config
// --reads 'data/*_{1,2}.fastq.gz' --outdir 'results'

// log info
//log.info("FASTQ pattern: {$params.reads}")

// 1. Definición de parámetros de entrada
params.reads = "data/PRJEB79238/*_{1,2}"
params.adapters = "/path/to/adapters/TruSeq3-PE.fa"
params.outdir = "results"

process TRIMMOMATIC {
    tag "$sample_id"
    publishDir "${params.outdir}/trimmed_reads", mode: 'copy'

    input:
    tuple val(sample_id), path(reads)

    output: 
    tuple val(sample_id), path("${sample_id}_*.fastq.gz"),
    emit: reads

    path "${sample_id}_*.fastq.gz",
    emit: logs
    
    script:
    """
    ${params.trimmomatic} PE -phred33 \\
    ${sample_id}_1.fastq.gz ${sample_id}_2.fastq.gz \\
    ${sample_id}_1_pair.fastq.gz ${sample_id}_1_upair.fastq.gz \\
    ${sample_id}_2_pair.fastq.gz ${sample_id}_2_upair.fastq.gz \\
    LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36
    """
    // ILLUMINACLIP:${params.adapters}:2:30:10 \\ find adaptor or find a program to infer

    /*
    echo "Muestra: ${sample_id}" > ${sample_id}.txt
    echo "R1: ${reads[0]}"      >> ${sample_id}.txt
    echo "R2: ${reads[1]}"      >> ${sample_id}.txt
    */
}

/*
process BBDUK {

}

process FASTP {
    
}
*/

workflow {
    // 2. Crear el canal a partir de los archivos de entrada
    read_pairs_ch = channel
        .fromFilePairs(params.reads, checkIfExists: true)

    // 3. Ejecutar el proceso
    TRIMMOMATIC(read_pairs_ch)
}