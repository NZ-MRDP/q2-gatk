import os
import subprocess
from typing import Union

from q2_types.feature_data._format import DNAFASTAFormat
from q2_types_genomics.per_sample_data._format import BAMDirFmt, BAMFormat

from ._format import VCFDirFormat, VCFFileFormat

# -ploidy {str(ploidy)}
# -bamout {bam_realigned_file}


def haplotype_caller(
    alignment_map: BAMDirFmt,
    reference_fasta: DNAFASTAFormat,
    emit_ref_confidences: str = None,
) -> BAMDirFmt:
    """haplotype_caller."""
    vcf = VCFDirFormat()
    for path, _ in alignment_map.bams.iter_views(view_type=BAMFormat):  # type: ignore
        cmd = [
            "gatk",
            "HaplotypeCaller",
            "-I",
            os.path.join(str(alignment_map.path), str(path.stem) + ".bam"),
            "-R",
            str(reference_fasta),
            "-O",
            os.path.join(str(vcf), str(path.stem) + ".bam"),
        ]
        if emit_ref_confidences:
            cmd.extend(["-ERC", str(emit_ref_confidences)])
        subprocess.run(cmd, check=True)
    return vcf
