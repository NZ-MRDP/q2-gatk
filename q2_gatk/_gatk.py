import os
import shutil
import subprocess
import tempfile
from typing import Union

from q2_samtools._format import (SamtoolsIndexFileFormat,
                                 SamtoolsIndexSequencesDirectoryFormat)
from q2_types.feature_data._format import DNAFASTAFormat
from q2_types_genomics.per_sample_data._format import BAMDirFmt, BAMFormat
from qiime2 import Metadata
from qiime2.plugin import ValidationError

from ._format import (BAMIndexAlignmentDirectoryFormat, BamIndexFileFormat,
                      DictDirFormat, DictFileFormat, MetricsDirFormat,
                      MetricsFileFormat, VCFDirFormat, VCFFileFormat)


#needs to be tested
#bam index and bam files need to be matched - do it similar to fasta and fai?
def haplotype_caller(
    deduplicated_bam: BAMIndexAlignmentDirectoryFormat,
    reference_fasta: SamtoolsIndexSequencesDirectoryFormat,
    emit_ref_confidence: str = None,
    ploidy: int = 2,
) -> (VCFDirFormat, BAMDirFmt):
    """haplotype_caller."""
    vcf = VCFDirFormat()
    realigned_bam = BAMDirFmt()
    for path, _ in deduplicated_bam.bams.iter_views(view_type=BAMFormat):  # type: ignore
            cmd = [
                "gatk",
                "HaplotypeCaller",
                "-I",
                os.path.join(str(deduplicated_bam.path), str(path.stem) + ".bam"),
                "-R",
                os.path.join(str(reference_fasta), reference_fasta.reference_fasta.name + ".fasta"),
                "-ploidy",
                str(ploidy),
                "--read-index",
                os.path.join(str(deduplicated_bam), deduplicated_bam.path.name + ".bai"),
#                os.path.join(str(bam_index.path), str(path.stem) + ".bai"),
                "-bamout",
                os.path.join(str(realigned_bam), str(path.stem) + ".bam"),
                "-O",
                os.path.join(str(vcf), str(path.stem) + ".vcf"),
            ]
            if emit_ref_confidence:
                cmd.extend(["-ERC", str(emit_ref_confidence)])
            subprocess.run(cmd, check=True)
    return vcf, realigned_bam

#Working
def create_seq_dict(
    reference_fasta: DNAFASTAFormat,
) -> DictDirFormat:
    """create_seq_dict."""
    dict = DictDirFormat()
    cmd = [
        "gatk",
        "CreateSequenceDictionary",
        "-R",
        str(reference_fasta),
        "-O",
        os.path.join(str(dict), "fasta.dict"),
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
# TODO: test with mulitple files

def build_bam_index(
    coordinate_sorted_bam: BAMDirFmt,
) -> BAMIndexAlignmentDirectoryFormat: 
    """build_bam_index."""
    bam_index = BAMIndexAlignmentDirectoryFormat()
    for path, _ in coordinate_sorted_bam.bams.iter_views(view_type=BAMFormat):
        bam_path = os.path.join(str(coordinate_sorted_bam), str(path))
        cmd = [
            "gatk",
            "BuildBamIndex",
            "-I",
            bam_path,
            "-O",
            os.path.join(str(bam_index),
                     os.path.basename(str(path) + ".bai")),
        ]
        try:
            subprocess.run(cmd, check=True)
            shutil.copyfile(bam_path, 
                        os.path.join(str(bam_index),
                                     os.path.basename(bam_path)))
        except subprocess.CalledProcessError as e:
            raise ValidationError("An error occurred while running GATK BuildBamIndex: %s" % str(e))
    return bam_index
