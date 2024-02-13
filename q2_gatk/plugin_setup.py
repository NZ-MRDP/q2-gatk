"""QIIME 2 plugin for gatk."""

import qiime2.plugin
from q2_types.feature_data import FeatureData
from q2_types.sample_data import SampleData
from q2_types_genomics.per_sample_data._type import AlignmentMap
from q2_types_variant import BAMIndexAlignment, Metrics, SequenceIndex, Variants
from qiime2.plugin import Int, Str

import q2_gatk

from . import __version__

plugin = qiime2.plugin.Plugin(
    name="gatk",
    version=__version__,
    description="QIIME 2 plugin for gatk",
    website="https://gatk.broadinstitute.org/hc/en-us",
    package="q2_gatk",
    user_support_text=("I'm sorry you're having problems"),
    citation_text=("https://genome.cshlp.org/content/20/9/1297"),
)

plugin.methods.register_function(
    function=q2_gatk.haplotype_caller,
    inputs={"deduplicated_bam": FeatureData[BAMIndexAlignment], "reference_fasta": FeatureData[SequenceIndex]},
    parameters={
        "emit_ref_confidence": Str,
        "ploidy": Int,
    },
    outputs={"vcf": FeatureData[Variants], "realigned_bam": FeatureData[BAMIndexAlignment]},
    input_descriptions={
        "deduplicated_bam": (
            "Input should be a deduplicated bam file imported as a qza. A separate q2 plugin is "
            "planned to convert between bam, sam, and cram formats."
        ),
        "reference_fasta": ("Reference DNA sequence FASTA. reference_fasta.fasta.fai must be in the same directory."),
    },
    parameter_descriptions={
        "emit_ref_confidence": (
            "The reference confidence mode makes it possible to emit a per-bp or summarized confidence estimate "
            "for a site being strictly homozygous-reference. See "
            "https://software.broadinstitute.org/gatk/documentation/article.php?id=4017 for information about GVCFs. "
            "For Mutect2, this is a BETA feature that functions similarly to the HaplotypeCaller reference "
            "confidence/GVCF mode. emit_ref_confidence argument can have one of the following values: "
            "NONE = Regular calling without emitting reference confidence calls "
            "BP_RESOLUTION = Reference model emitted site by site "
            "GVCF = Reference model emitted with condensed non-variant blocks, i.e. the GVCF format "
            "ReferenceConfidenceMode = NONE"
        ),
        "ploidy": (
            "Ploidy (number of chromosomes) per sample. For pooled data, set to "
            "(Number of samples in each pool * Sample Ploidy)."
        ),
    },
    output_descriptions={
        "vcf": (
            "Either a VCF or GVCF file with raw, unfiltered SNP and indel calls. Regular VCFs must be filtered either "
            "by variant recalibration (Best Practice) or hard-filtering before use in downstream analyses. If using "
            "the GVCF workflow, the output is a GVCF file that must first be run through GenotypeGVCFs and then "
            "filtering before further analysis."
        ),
        "realigned_bam": "File to which assembled haplotypes should be written.",
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
    parameters={},
    outputs=[
        ("deduplicated_bam", SampleData[AlignmentMap]),
        ("metrics", FeatureData[Metrics]),
    ],
    input_descriptions={
        "sorted_bam": "The sorted input BAM file containing reads to mark duplicates.",
    },
    parameter_descriptions={},
    output_descriptions={
        "deduplicated_bam": "A new BAM in which duplicates have been identified in the SAM flags field for each read. "
        "Duplicates are marked with the hexadecimal value of 0x0400, which corresponds to a decimal value of 1024",
        "metrics": "File indicating the numbers of duplicates for both single- and paired-end reads",
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
    },
    outputs=[
        ("sorted_bam", SampleData[AlignmentMap]),
    ],
    input_descriptions={
        "input_bam": "The input BAM file containing reads to mark duplicates.",
    },
    parameter_descriptions={
        "sort_order": "Optional sort order to output in. If not supplied, OUTPUT is in the same order as INPUT. "
        "Options include unsorted, queryname, coordinate, duplicate, or  unknown",
        "library": "Read group library",
        "platform": "Read group platform (e.g, Illumina, Solid)",
        "platform_unit": "Read group platform unit (e.g., run barcode)",
    },
    output_descriptions={
        "sorted_bam": "A new BAM in which duplicates have been identified in the SAM flags field for each read. "
        "Duplicates are marked with the hexadecimal value of 0x0400, which corresponds to a decimal value of 1024",
    },
    name="Assigns all the reads in a file to a single new read-group",
    description=(
        "Many tools (Picard and GATK for example) require or assume the presence of at least one RG tag, "
        "defining a read-group to which each read can be assigned (as specified in the RG tag in the SAM record). "
        "This tool enables the user to assign all the reads in the {@link #INPUT} to a single new read-group."
    ),
)

plugin.methods.register_function(
    function=q2_gatk.build_bam_index,
    inputs={
        "coordinate_sorted_bam": SampleData[AlignmentMap],
    },
    parameters={},
    outputs=[
        ("bam_index", FeatureData[BAMIndexAlignment]),
    ],
    input_descriptions={
        "coordinate_sorted_bam": "The input BAM file sorted in coordinate order.",
    },
    parameter_descriptions={},
    output_descriptions={
        "bam_index": "The BAM index file. Defaults to x.bai if INPUT is x.bam, otherwise INPUT.bai.",
    },
    name="Generates a BAM index .bai file.",
    description=(
        "This tool creates an index file for the input BAM that allows fast look-up of data in a BAM file, like an "
        "index on a database. Note that this tool cannot be run on SAM files, and that the input BAM file must be "
        "sorted in coordinate order."
    ),
)
