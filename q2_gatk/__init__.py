"""gatk python library."""

from ._gatk import (
    add_replace_read_groups,
    build_bam_index,
    haplotype_caller,
    mark_duplicates,
)

__version__ = "0.1.7"

__all__ = ["haplotype_caller", "mark_duplicates", "add_replace_read_groups", "build_bam_index"]
