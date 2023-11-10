"""gatk python library."""
from ._gatk import create_seq_dict, haplotype_caller, mark_duplicates
from ._type import DictFormat, MetricsFormat, VCFFormat

__version__ = "0.0.0"

__all__ = ["haplotype_caller", "create_seq_dict", "mark_duplicates"]
