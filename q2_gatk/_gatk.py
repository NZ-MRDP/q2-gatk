import os
import subprocess
from typing import Union

from q2_types.feature_data._format import DNAFASTAFormat
from q2_types_genomics.per_sample_data._format import BAMDirFmt, BAMFormat
from qiime2 import Metadata
from qiime2.plugin import ValidationError

from ._format import (BamIndexDirFormat, BamIndexFileFormat, DictDirFormat,
                      DictFileFormat, MetricsDirFormat, MetricsFileFormat,
                      VCFDirFormat, VCFFileFormat)


#needs to be tested
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

#Not working and I do not know why. I think because the input and output are files (not dirs), the file formats are correct here, as are the cmd inputs, but not sure
def create_seq_dict(
    reference_fasta: DNAFASTAFormat,
) -> DictFileFormat:
    """create_seq_dict."""
    dict = DictFileFormat()
    cmd = [
        "gatk",
        "CreateSequenceDictionary",
        "-R",
        str(reference_fasta),
        "-O",
        str(dict),
        ]
    subprocess.run(cmd, check=True)
    return dict

#working!
def mark_duplicates(
    sorted_bam: BAMDirFmt,
) -> (BAMDirFmt, MetricsFileFormat):
    """mark_duplicates."""
    deduplicated_bam = BAMDirFmt()
    metrics = MetricsFileFormat()
    for path, _ in sorted_bam.bams.iter_views(view_type=BAMFormat):  # type: ignore
        cmd = [
            "gatk", 
            "MarkDuplicates", 
            "-I",
            os.path.join(str(sorted_bam.path), str(path.stem) + ".bam"),
            "-M", 
            str(metrics),
            "-O", 
            os.path.join(str(deduplicated_bam), str(path.stem) + ".bam"),
        ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise ValidationError("An error occurred while running GATK MarkDuplicates: %s" % str(e))

    return deduplicated_bam, metrics

#working :)
def add_replace_read_groups(
    input_bam: BAMDirFmt,
    library: str,
    platform_unit: str,
    platform: str,
    sample_name: str,
    sort_order: str = None,  # type: ignore
) -> BAMDirFmt:
    """add_replace_read_groups."""
    sorted_bam = BAMDirFmt()
    for path, _ in input_bam.bams.iter_views(view_type=BAMFormat):  # type: ignore
        cmd = [
            "gatk",
            "AddOrReplaceReadGroups",
            "-I",
            os.path.join(str(input_bam.path), str(path.stem) + ".bam"),
            "-O",
            os.path.join(str(sorted_bam), str(path.stem) + ".bam"),
            "-SO",
            sort_order,
            "-PU",
            platform_unit,
            "-LB",
            library,
            "-PL",
            platform,
            "-SM",
            sample_name,
        ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise ValidationError("An error occurred while running GATK AddOrReplaceReadGroups: %s" % str(e))

    return sorted_bam


# TODO: Add flags if desired

#not working - needs a transformer, which I do not know how to do
def build_bam_index(
    coordinate_sorted_bam: BAMDirFmt,
) -> BamIndexDirFormat: # type: ignore
    """build_bam_index."""
    bam_index = BamIndexDirFormat()
    for path, _ in coordinate_sorted_bam.bams.iter_views(view_type=BAMFormat):  # type: ignore
        cmd = [
            "gatk",
            "BuildBamIndex",
            "-I",
            os.path.join(str(coordinate_sorted_bam.path), str(path.stem) + ".bam"),
            "-O",
            os.path.join(str(bam_index), str(path.stem) + ".bai"),
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValidationError("An error occurred while running GATK BuildBamIndex: %s" % str(e))
        return bam_index
