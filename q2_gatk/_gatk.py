import os
import subprocess
from typing import Union

from q2_types.feature_data._format import DNAFASTAFormat
from q2_types_genomics.per_sample_data._format import BAMDirFmt, BAMFormat
from qiime2 import Metadata
from qiime2.plugin import ValidationError

from ._format import DictDirFormat, DictFileFormat, VCFDirFormat, VCFFileFormat


def haplotype_caller(
    alignment_map: BAMDirFmt,
    reference_fasta: DNAFASTAFormat,
    emit_ref_confidence: str = None,
    ploidy: int = 2,
) -> (VCFDirFormat, BAMDirFmt):
    """haplotype_caller."""
    vcf = VCFDirFormat()
    bam = BAMDirFmt()
    for path, _ in alignment_map.bams.iter_views(view_type=BAMFormat):  # type: ignore
        cmd = [
            "gatk",
            "HaplotypeCaller",
            "-I",
            os.path.join(str(alignment_map.path), str(path.stem) + ".bam"),
            "-R",
            str(reference_fasta),
            "-ploidy",
            str(ploidy),
            "-bamout",
            os.path.join(str(bam), str(path.stem) + ".bam"),
            "-O",
            os.path.join(str(vcf), str(path.stem) + ".vcf"),
        ]
        if emit_ref_confidence:
            cmd.extend(["-ERC", str(emit_ref_confidence)])
        subprocess.run(cmd, check=True)
    return vcf, bam


def create_seq_dict(
    reference_fasta: DNAFASTAFormat,
) -> DictDirFormat:
    """create_seq_dict."""
    dict = DictDirFormat()
    for path, _ in reference_fasta.bams.iter_views(view_type=DNAFASTAFormat):  # type: ignore
        cmd = [
            "gatk",
            "CreateSequenceDictionary",
            "-R",
            os.path.join(str(reference_fasta.path), str(path.stem) + ".fasta"),
            "-O",
            os.path.join(str(dict), str(path.stem) + ".dict"),
        ]
        subprocess.run(cmd, check=True)
    return dict


# Define the function
def mark_duplicates(
    bam: BAMDirFmt,
) -> (BAMDirFmt, Metadata):
    """mark_duplicates."""
    deduplicated_bam = BAMDirFmt()
    metrics = Metadata
    for path, _ in alignment_map.bams.iter_views(view_type=BAMFormat):  # type: ignore
        cmd = ["gatk", "MarkDuplicates", "-I", str(bam), "-M", str(metrics), "-O", str(deduplicated_bam)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise ValidationError("An error occurred while running GATK MarkDuplicates: %s" % str(e))

    return deduplicated_bam, metrics
