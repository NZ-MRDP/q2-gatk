import os
import shutil
import subprocess
from pathlib import Path

from q2_types_genomics.per_sample_data._format import BAMDirFmt, BAMFormat
from q2_types_variant import (
    BAMIndexAlignmentDirectory,
    MetricsFile,
    SamtoolsIndexSequencesDirectoryFormat,
    VCFIndexDirectory,
)
from qiime2.plugin import ValidationError


# currently being tested
def haplotype_caller(
    deduplicated_bam: BAMIndexAlignmentDirectory,
    reference_fasta: SamtoolsIndexSequencesDirectoryFormat,
    emit_ref_confidence: str = None,
    ploidy: int = 2,
) -> (VCFIndexDirectory, BAMIndexAlignmentDirectory):
    """haplotype_caller."""
    vcf = VCFIndexDirectory()
    realigned_bam = BAMIndexAlignmentDirectory()

    for bam, bai in zip(deduplicated_bam.bam_file_paths, deduplicated_bam.bai_file_paths):
        cmd = [
            "gatk",
            "HaplotypeCaller",
            "-I",
            bam,
            "-R",
            reference_fasta.reference_fasta_filepath,
            "-ploidy",
            str(ploidy),
            "--read-index",
            bai,
            "-bamout",
            os.path.join(str(realigned_bam), os.path.basename(bam)),
            "-O",
            os.path.join(str(vcf), Path(bam).stem + ".vcf"),
        ]

        if emit_ref_confidence:
            cmd.extend(["-ERC", str(emit_ref_confidence)])

        subprocess.run(cmd, check=True)

    return vcf, realigned_bam


# test whether function fails if one sample fails by replacing one of the bam files with an invalid file
def mark_duplicates(
    sorted_bam: BAMDirFmt,
) -> (BAMDirFmt, MetricsFile):
    """mark_duplicates."""
    deduplicated_bam = BAMDirFmt()
    metrics = MetricsFile()

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


# working :)
def add_replace_read_groups(
    input_bam: BAMDirFmt,
    library: str,
    platform_unit: str,
    platform: str,
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
            str(path.stem),
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValidationError("An error occurred while running GATK AddOrReplaceReadGroups: %s" % str(e))

    return sorted_bam


# TODO: Add flags if desired


def build_bam_index(
    coordinate_sorted_bam: BAMDirFmt,
) -> BAMIndexAlignmentDirectory:
    """build_bam_index."""
    bam_index = BAMIndexAlignmentDirectory()

    for path, _ in coordinate_sorted_bam.bams.iter_views(view_type=BAMFormat):
        bam_path = os.path.join(str(coordinate_sorted_bam), str(path))
        cmd = [
            "gatk",
            "BuildBamIndex",
            "-I",
            bam_path,
            "-O",
            os.path.join(
                str(bam_index), Path(path).stem + ".bai"
            ),  # output formatting needs to change to work with new bamindexalignmentdirectoryformat attributes
        ]

        try:
            subprocess.run(cmd, check=True)
            shutil.copyfile(bam_path, os.path.join(str(bam_index), os.path.basename(bam_path)))
        except subprocess.CalledProcessError as e:
            raise ValidationError("An error occurred while running GATK BuildBamIndex: %s" % str(e))

    return bam_index
