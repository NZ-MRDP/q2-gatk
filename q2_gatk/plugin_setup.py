"""Register GATK methods with the QIIME 2 plugin system."""

import qiime2.plugin
from q2_types.feature_data import FeatureData
from q2_types.per_sample_sequences import AlignmentMap
from q2_types.sample_data import SampleData
from q2_types_variant import BAMIndexAlignment, Metrics, SequenceIndex, Variants
from qiime2.plugin import Bool, Choices, Float, Int, Str

import q2_gatk

from . import __version__

plugin = qiime2.plugin.Plugin(
    name="gatk",
    version=__version__,
    description="QIIME 2 plugin for GATK variant calling",
    website="https://gatk.broadinstitute.org/hc/en-us",
    package="q2_gatk",
    user_support_text=(
        "Please post questions or bug reports to the GitHub issue tracker: "
        "https://github.com/NZ-MRDP/q2-gatk/issues"
    ),
    citation_text=(
        "McKenna A, Hanna M, Banks E, et al. The Genome Analysis Toolkit: "
        "A MapReduce framework for analyzing next-generation DNA sequencing data. "
        "Genome Research. 2010;20(9):1297-1303. doi:10.1101/gr.107524.110"
    ),
)

plugin.methods.register_function(
    function=q2_gatk.haplotype_caller,
    inputs={"deduplicated_bam": FeatureData[BAMIndexAlignment], "reference_fasta": FeatureData[SequenceIndex]},
    parameters={
        "emit_ref_confidence": Str,
        "ploidy": Int,
        "intervals": Str,
        "interval_padding": Int,
        "native_pair_hmm_threads": Int,
        "output_mode": Str % Choices(["EMIT_VARIANTS_ONLY", "EMIT_ALL_ACTIVE_SITES"]),
        "pcr_indel_model": Str % Choices(["NONE", "HOSTILE", "AGGRESSIVE", "CONSERVATIVE"]),
        "min_call_confidence": Float,
    },
    outputs={"vcf": FeatureData[Variants], "realigned_bam": FeatureData[BAMIndexAlignment]},
    input_descriptions={
        "deduplicated_bam": "Coordinate-sorted BAM alignments bundled with matching BAM index files (.bai).",
        "reference_fasta": "Indexed reference sequences containing the FASTA, .fai, and sequence dictionary files.",
    },
    parameter_descriptions={
        "emit_ref_confidence": (
            "Reference-confidence mode. Use `GVCF` for cohort workflows, `BP_RESOLUTION` to emit "
            "site-by-site confidence estimates, or omit the parameter for standard VCF calling."
        ),
        "ploidy": (
            "Ploidy (number of chromosomes) per sample. For pooled data, set to "
            "(Number of samples in each pool * Sample Ploidy)."
        ),
        "intervals": "Restrict calling to one or more genomic intervals, for example `chr1` or `chr1:1000-2000`.",
        "interval_padding": "Number of base pairs to pad on each side of the requested intervals.",
        "native_pair_hmm_threads": "Number of native PairHMM threads used by HaplotypeCaller.",
        "output_mode": "Choose whether to emit only variant sites or all active sites considered during calling.",
        "pcr_indel_model": "Model used to penalize indels that are likely caused by PCR amplification artifacts.",
        "min_call_confidence": "Minimum phred-scaled confidence threshold required to emit a variant call.",
    },
    output_descriptions={
        "vcf": (
            "Raw single-sample variant calls produced by HaplotypeCaller. When `emit_ref_confidence=GVCF`, "
            "the output should be joint-genotyped before downstream analysis."
        ),
        "realigned_bam": "Per-sample BAM alignments with assembled haplotypes written by HaplotypeCaller.",
    },
    name="Call germline SNPs and indels via local re-assembly of haplotypes",
    description=(
        "The HaplotypeCaller is capable of calling SNPs and indels simultaneously via local de-novo assembly of "
        "haplotypes in an active region. In other words, whenever the program encounters a region showing signs of "
        "variation, it discards the existing mapping information and completely reassembles the reads in that "
        "region. This allows the HaplotypeCaller to be more accurate when calling regions that are traditionally "
        "difficult to call, for example when they contain different types of variants close to each other. It also "
        "makes the HaplotypeCaller much better at calling indels than position-based callers like UnifiedGenotyper."
    ),
)

plugin.methods.register_function(
    function=q2_gatk.mark_duplicates,
    inputs={"sorted_bam": SampleData[AlignmentMap]},
    parameters={
        "remove_duplicates": Bool,
        "optical_duplicate_pixel_distance": Int,
        "validation_stringency": Str % Choices(["STRICT", "LENIENT", "SILENT"]),
    },
    outputs=[
        ("deduplicated_bam", SampleData[AlignmentMap]),
        ("metrics", FeatureData[Metrics]),
    ],
    input_descriptions={
        "sorted_bam": "Coordinate-sorted BAM alignments to scan for PCR and optical duplicates.",
    },
    parameter_descriptions={
        "remove_duplicates": "Remove duplicate reads instead of only marking them in the SAM flags.",
        "optical_duplicate_pixel_distance": (
            "Pixel distance used to identify optical duplicates on patterned flowcells."
        ),
        "validation_stringency": "Validation strictness used when reading the input BAM files.",
    },
    output_descriptions={
        "deduplicated_bam": (
            "BAM alignments with duplicate reads flagged or removed, depending on `remove_duplicates`."
        ),
        "metrics": "Picard duplicate metrics summarizing duplicate rates and optical duplicate counts.",
    },
    name="Identifies duplicate reads",
    description=(
        "Locates and tags duplicate reads in a BAM file, where duplicate reads are defined as originating from a "
        "single fragment of DNA. Duplicates can arise during sample preparation e.g. library construction using PCR. "
        "Duplicate reads can also result from a single amplification cluster, incorrectly detected as multiple "
        "clusters by the optical sensor of the sequencing instrument. These duplication artifacts are referred to "
        "as optical duplicates. The MarkDuplicates tool works by comparing sequences in the 5 prime positions of "
        "both reads and read-pairs in a BAM file. After duplicate reads are collected, the tool differentiates the "
        "primary and duplicate reads using an algorithm that ranks reads by the sums of their base-quality scores "
        "(default method). Note that this is different from directly checking if the sequences match, which "
        "MarkDuplicates does not do."
    ),
)

plugin.methods.register_function(
    function=q2_gatk.add_replace_read_groups,
    inputs={
        "input_bam": SampleData[AlignmentMap],
    },
    parameters={
        "sort_order": Str,
        "library": Str,
        "platform": Str,
        "platform_unit": Str,
        "sample_name": Str,
        "read_group_id": Str,
        "sequencing_center": Str,
        "platform_model": Str,
        "description": Str,
        "program_group": Str,
    },
    outputs=[
        ("sorted_bam", SampleData[AlignmentMap]),
    ],
    input_descriptions={
        "input_bam": "BAM alignments whose reads should all be assigned to a new read group.",
    },
    parameter_descriptions={
        "sort_order": "Optional output sort order. If omitted, the input order is preserved.",
        "library": "Read-group library name (`RGLB`).",
        "platform": "Read-group platform (`RGPL`), for example `ILLUMINA` or `PACBIO`.",
        "platform_unit": "Read-group platform unit (`RGPU`), often flowcell, lane, or barcode information.",
        "sample_name": "Read-group sample name (`RGSM`). Defaults to the BAM basename when omitted.",
        "read_group_id": "Read-group identifier (`RGID`). Defaults to the BAM basename when omitted.",
        "sequencing_center": "Sequencing center identifier (`RGCN`).",
        "platform_model": "Platform model (`RGPM`), for example instrument model.",
        "description": "Free-text read-group description (`RGDS`).",
        "program_group": "Program group recorded in the read group (`RGPG`).",
    },
    output_descriptions={
        "sorted_bam": "BAM alignments with a consistent single read group assigned to every read.",
    },
    name="Assigns all the reads in a file to a single new read-group",
    description=(
        "Many tools (Picard and GATK for example) require or assume the presence of at least one RG tag, "
        "defining a read-group to which each read can be assigned (as specified in the RG tag in the SAM record). "
        "This tool enables the user to assign all the reads in the input BAM to a single new read-group."
    ),
)

plugin.methods.register_function(
    function=q2_gatk.build_bam_index,
    inputs={
        "coordinate_sorted_bam": SampleData[AlignmentMap],
    },
    parameters={
        "validation_stringency": Str % Choices(["STRICT", "LENIENT", "SILENT"]),
        "verbosity": Str % Choices(["ERROR", "WARNING", "INFO", "DEBUG"]),
    },
    outputs=[
        ("bam_index", FeatureData[BAMIndexAlignment]),
    ],
    input_descriptions={
        "coordinate_sorted_bam": "Coordinate-sorted BAM alignments to index.",
    },
    parameter_descriptions={
        "validation_stringency": "Validation strictness used while reading each BAM before indexing.",
        "verbosity": "GATK/Picard logging verbosity during indexing.",
    },
    output_descriptions={
        "bam_index": "Indexed BAM alignments containing both each `.bam` file and its matching `.bai` file.",
    },
    name="Generates a BAM index .bai file.",
    description=(
        "This tool creates an index file for the input BAM that allows fast look-up of data in a BAM file, like an "
        "index on a database. Note that this tool cannot be run on SAM files, and that the input BAM file must be "
        "sorted in coordinate order."
    ),
)
