nextflow.enable.dsl=2

// run with: nextflow run flows/spadesflow.nf -c flows/spadesflow.config -profile local
// it takes more than 3 hours to get a 20%

process MSPADES {
    tag "$sample_id"
    cpus 4
    memory '6 GB'
    container 'staphb/spades:latest'

    publishDir "${params.outdir}", mode: 'copy'

    input:
    tuple val(sample_id), path(r1), path(r2)//, path(unpaired_reads)

    output:
    tuple val(sample_id), path("${sample_id}_metaspades")

    script:
    """
    metaspades.py \\
      -1 $r1 \\
      -2 $r2 \\
      -o ${sample_id}_metaspades \\
      --threads ${task.cpus} \\
      --memory 6
      --bam
    """

//      # -s $unpaired_reads -o ${sample_id}_metaspades\\
}
workflow {
    // Paired-end
    paired_ch = channel.fromFilePairs(
        params.reads,
        size: 2,
        checkIfExists: true
    )
    .map { sid, reads ->
        tuple(sid, reads[0], reads[1])
    }

    // paired_ch.view()
    /*
    unpaired_ch = channel.empty()
    if( params.unpaired ) {
        unpaired_ch = channel.fromPath(params.unpaired, checkIfExists: true)
            .map { f ->
                def sid = f.baseName.replaceAll(/_\d_upair.fastq/, '')
                tuple(sid, f)
            }
            .groupTuple()
    }
    */
    //unpaired_ch.view()

    //reads_ch = paired_ch.map { sid, r1, r2 -> tuple(sid, r1, r2, []) }
    
    //reads_ch.view()
    
    //reads_ch = paired_ch.join(unpaired_ch, by: 0)
    //    .map { sid, r1, r2, upairs -> tuple(sid, r1, r2, upairs) }

    //reads_ch.view()

    MSPADES(paired_ch)
}