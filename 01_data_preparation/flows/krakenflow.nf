nextflow.enable.dsl=2

// run with nextflow run krakenflow -c krakenflow.config --reads 'data/*_{1,2}.fastq.gz' --outdir 'results'

// log info
//log.info("FASTQ pattern: {$params.reads}")


process KRAKEN2 {
    tag "$sample_id"
    publishDir "results/kmer/${params.outdir}", mode: 'copy'

    input:
    tuple val(sample_id), path(reads)

    output: 
    tuple val(sample_id), 
    path("${sample_id}.output"), 
    path("${sample_id}-mpa.report")
    
    // emit: reads 
    
    script:
    """
    echo "Ejecutando Kraken con el archivo: ${reads}" 
    kraken2 \\
    --db '/home/mikdat/silva_db' \\
    --gzip-compressed \\
    --confidence ${params.confidence} \\
    --output ${sample_id}.output \\
    --report ${sample_id}-mpa.report \\
    ${sample_id}
    """
}

workflow {
    // 2. Crear el canal a partir de los archivos de entrada
    read_ch = channel
        .fromPath(params.reads, checkIfExists: true)
        .map { file -> tuple(file.name, file) }
    // 3. Ejecutar el proceso
    KRAKEN2(read_ch)
}