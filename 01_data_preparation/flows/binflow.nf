nextflow.enable.dsl=2

// need to rename the contigs
// run with: nextflow flows/binflow.nf -c flows/binflow.config -profile docker


process RENAME {
    tag "$sample"
    publishDir "${params.renameOutput}", mode: 'copy'

    
    input:
    tuple val(sample), path(input_fasta)

    output:
    tuple val(sample), path("${sample}.fasta")

    script:
    """
    cp $input_fasta ${sample}.fasta
    """
}

// for samtools install first:
// sudo apt-get install -y libncurses-dev libbz2-dev liblzma-dev
// wget https://github.com/samtools/samtools/releases/download/1.20/samtools-1.20.tar.bz2
// tar xvjf samtools-1.20.tar.bz2
// cd samtools-1.20/
// ./configure
// make
// sudo make install
// export PATH="$PATH:$HOME/samtools-1.20"
process BWA {
    tag "${sample_id}"
    
    cpus params.cpus
    memory params.memory
    publishDir 'results/asemb/contigs/bam', mode: 'copy'
    
    input:
    tuple val(sample_id), path(contigs), path(r1), path(r2)


    
    output:
    tuple val(sample_id),
        path(contigs),
        path("${sample_id}.bam"),
        path("${sample_id}.bam.bai"),
        path("${sample_id}.idxstats"),
        path("${sample_id}.abundance.tsv")

    script:
    """
    cp ${contigs} ref_${contigs}.fasta
    echo 'indexing contigs...'
    bwa index ${contigs}
    echo 'Ordering contigs...'
    bwa mem ${contigs} ${r1} ${r2} | samtools sort -o ${sample_id}.bam
    samtools index  ${sample_id}.bam
    samtools idxstats ${sample_id}.bam > ${sample_id}.idxstats
    samtools idxstats ${sample_id}.bam | \
    awk '{split(\$1,a,"_"); mag=a[1]; count[mag]+=\$3} \
    END {for (m in count) print m "\\t" count[m]}' \
    | sort > ${sample_id}.abundance.tsv
    echo 'moving indexed  ordered bam...'
    """
    // mv ${sample_id}.bam* contigs/bam/
}


/*
process METABAT {
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
    metabat --help
    # 2. Calcular cobertura
    jgi_summarize_bam_contig_depths --outputDepth {$sample_id}_depth.txt {$sample_id}.bam
    # 3. Binning con MetaBAT2
    metabat2 -i {$sample_id}_metaspades.fasta -a {$sample_id}_depth.txt -o bins/bin
    """
    
}
*/
/*
process CHECKM2 {
    tag "$sample_id"
    publishDir "${params.outdir}/trimmed_reads", mode: 'copy'

    input:
    tuple val(sample_id), path(reads)
}
*/
workflow {

    // for the output of spades
    read_ch = channel
        .fromPath(params.renameInput, checkIfExists: true)
        .map { file ->
            def dirname = file.parent.baseName
            def sid = dirname.split('_')[0]
            tuple(sid, file)
        }

    //read_ch.view()

    // need the input of spades for bwa
    paired_ch = channel.fromFilePairs(
        params.reads,
        size: 2,
        checkIfExists: true
    )
    .map { sid, reads ->
        tuple(sid, reads[0], reads[1])
    }

    join_ch = read_ch.join(paired_ch, by: 0) 

    // join_ch.view()

    //RENAME(read_ch)
    BWA(join_ch)

}