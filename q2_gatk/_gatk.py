"""GATK actions used by the QIIME 2 plugin."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from q2_types.per_sample_sequences import BAMDirFmt, BAMFormat
from q2_types_variant import (
    BAMIndexAlignmentDirectory,
    MetricsFile,
    SamtoolsIndexSequencesDirectoryFormat,
    VCFIndexDirectory,
)
from qiime2.plugin import ValidationError


def haplotype_caller(
    deduplicated_bam: BAMIndexAlignmentDirectory,
    reference_fasta: SamtoolsIndexSequencesDirectoryFormat,
    emit_ref_confidence: Optional[str] = None,
    ploidy: int = 2,
    intervals: Optional[str] = None,
    interval_padding: Optional[int] = None,
    native_pair_hmm_threads: int = 1,
    output_mode: str = "EMIT_VARIANTS_ONLY",
    pcr_indel_model: str = "CONSERVATIVE",
    min_call_confidence: float = 30.0,
) -> Tuple[VCFIndexDirectory, BAMIndexAlignmentDirectory]:
    """Call germline SNPs and indels via local re-assembly of haplotypes.

    Runs GATK HaplotypeCaller on each BAM file in the input directory,
    producing a VCF (or GVCF) and a realigned BAM per sample.
    """
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
            "--native-pair-hmm-threads",
            str(native_pair_hmm_threads),
            "--output-mode",
            output_mode,
            "--pcr-indel-model",
            pcr_indel_model,
            "--standard-min-confidence-threshold-for-calling",
            str(min_call_confidence),
            "--read-index",
            bai,
            "-bamout",
            os.path.join(str(realigned_bam), os.path.basename(bam)),
            "-O",
            os.path.join(str(vcf), Path(bam).stem + ".vcf"),
        ]

        if emit_ref_confidence:
            cmd.extend(["-ERC", str(emit_ref_confidence)])
        if intervals:
            cmd.extend(["--intervals", intervals])
        if interval_padding is not None:
            cmd.extend(["--interval-padding", str(interval_padding)])

        subprocess.run(cmd, check=True)

    return vcf, realigned_bam


def mark_duplicates(
    sorted_bam: BAMDirFmt,
    remove_duplicates: bool = False,
    optical_duplicate_pixel_distance: Optional[int] = None,
    validation_stringency: str = "SILENT",
) -> Tuple[BAMDirFmt, MetricsFile]:
    """Identify and tag duplicate reads in a BAM file.

    Runs GATK MarkDuplicates on each BAM file in the input directory.
    Raises a ValidationError if GATK exits with a non-zero status.
    """
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
            "--VALIDATION_STRINGENCY",
            validation_stringency,
        ]
        if remove_duplicates:
            cmd.extend(["--REMOVE_DUPLICATES", "true"])
        if optical_duplicate_pixel_distance is not None:
            cmd.extend(["--OPTICAL_DUPLICATE_PIXEL_DISTANCE", str(optical_duplicate_pixel_distance)])

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as error:
            raise ValidationError(f"An error occurred while running GATK MarkDuplicates: {error}") from error

    return deduplicated_bam, metrics


def add_replace_read_groups(
    input_bam: BAMDirFmt,
    library: str,
    platform_unit: str,
    platform: str,
    sample_name: Optional[str] = None,
    read_group_id: Optional[str] = None,
    sequencing_center: Optional[str] = None,
    platform_model: Optional[str] = None,
    description: Optional[str] = None,
    program_group: Optional[str] = None,
    sort_order: Optional[str] = None,
) -> BAMDirFmt:
    """Assign all reads in a BAM file to a single new read-group.

    Runs GATK AddOrReplaceReadGroups on each BAM file in the input directory.
    Raises a ValidationError if GATK exits with a non-zero status.
    """
    sorted_bam = BAMDirFmt()

    for path, _ in input_bam.bams.iter_views(view_type=BAMFormat):  # type: ignore
        sample_id = sample_name or str(path.stem)
        group_id = read_group_id or str(path.stem)
        cmd = [
            "gatk",
            "AddOrReplaceReadGroups",
            "-I",
            os.path.join(str(input_bam.path), str(path.stem) + ".bam"),
            "-O",
            os.path.join(str(sorted_bam), str(path.stem) + ".bam"),
            "-PU",
            platform_unit,
            "-LB",
            library,
            "-PL",
            platform,
            "-RGID",
            group_id,
            "-SM",
            sample_id,
        ]
        if sort_order:
            cmd.extend(["-SO", sort_order])
        if sequencing_center:
            cmd.extend(["-CN", sequencing_center])
        if platform_model:
            cmd.extend(["-PM", platform_model])
        if description:
            cmd.extend(["-DS", description])
        if program_group:
            cmd.extend(["-PG", program_group])

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as error:
            raise ValidationError(f"An error occurred while running GATK AddOrReplaceReadGroups: {error}") from error

    return sorted_bam


# TODO: expose additional BuildBamIndex flags (e.g. --VERBOSITY, --VALIDATION_STRINGENCY)
def build_bam_index(
    coordinate_sorted_bam: BAMDirFmt,
    validation_stringency: str = "SILENT",
    verbosity: str = "INFO",
) -> BAMIndexAlignmentDirectory:
    """Build a BAM index (.bai) for each BAM file in the input directory.

    Runs GATK BuildBamIndex and copies the original BAM into the output
    directory alongside the generated index. Raises a ValidationError if
    GATK exits with a non-zero status.
    """
    bam_index = BAMIndexAlignmentDirectory()

    for path, _ in coordinate_sorted_bam.bams.iter_views(view_type=BAMFormat):
        bam_path = os.path.join(str(coordinate_sorted_bam), str(path))
        cmd = [
            "gatk",
            "BuildBamIndex",
            "-I",
            bam_path,
            "-O",
            # Output path format must align with BAMIndexAlignmentDirectory attributes
            os.path.join(str(bam_index), Path(path).stem + ".bai"),
            "--VALIDATION_STRINGENCY",
            validation_stringency,
            "--VERBOSITY",
            verbosity,
        ]

        try:
            subprocess.run(cmd, check=True)
            shutil.copyfile(bam_path, os.path.join(str(bam_index), os.path.basename(bam_path)))
        except subprocess.CalledProcessError as error:
            raise ValidationError(f"An error occurred while running GATK BuildBamIndex: {error}") from error

    return bam_index


haplotype_caller.__annotations__["return"] = (VCFIndexDirectory, BAMIndexAlignmentDirectory)
mark_duplicates.__annotations__["return"] = (BAMDirFmt, MetricsFile)
