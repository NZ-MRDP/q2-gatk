"""QIIME 2 plugin for gatk."""

import q2_gatk
import qiime2.plugin
from q2_types.feature_data import FeatureData, Sequence
from q2_types.sample_data import SampleData
from q2_types_genomics.per_sample_data._type import AlignmentMap
from qiime2.plugin import Int, Str

from ._format import DictDirFormat, DictFileFormat, VCFDirFormat, VCFFileFormat
from ._type import DictFormat, VCFFormat

plugin = qiime2.plugin.Plugin(
    name="gatk",
    version="0.0.0",
    description="QIIME 2 plugin for gatk",
    website="https://gatk.broadinstitute.org/hc/en-us",
    package="q2_gatk",
    user_support_text=("I'm sorry you're having problems"),
    citation_text=("https://genome.cshlp.org/content/20/9/1297"),
)

plugin.methods.register_function(
    function=q2_gatk.haplotype_caller,
    inputs={"alignment_map": SampleData[AlignmentMap], "reference_fasta": FeatureData[Sequence]},
    parameters={
        "emit_ref_confidence": Str,
        "ploidy": Int,
    },
    outputs={"vcf": FeatureData[VCFFormat], "bam": SampleData[AlignmentMap]},
    input_descriptions={
        "alignment_map": "Input should be a bam file imported as a qza. A separate q2 plugin is planned to convert between bam, sam, "
        "and cram formats.",
        "reference_fasta": ("Reference DNA sequence FASTA"),
    },
    parameter_descriptions={
        "emit_ref_confidence": "The reference confidence mode makes it possible to emit a per-bp or summarized confidence estimate "
        "for a site being strictly homozygous-reference. See https://software.broadinstitute.org/gatk/documentation/article.php?id=4017"
        " for information about GVCFs. For Mutect2, this is a BETA feature that functions similarly to the HaplotypeCaller reference "
        "confidence/GVCF mode. emit_ref_confidence argument can have one of the following values: "
        "NONE = Regular calling without emitting reference confidence calls "
        "BP_RESOLUTION = Reference model emitted site by site "
        "GVCF = Reference model emitted with condensed non-variant blocks, i.e. the GVCF format "
        "ReferenceConfidenceMode = NONE",
        "ploidy": "Ploidy (number of chromosomes) per sample. For pooled data, set to (Number of samples in each pool * Sample Ploidy).",
    },
    output_descriptions={
        "vcf": "Either a VCF or GVCF file with raw, unfiltered SNP and indel calls. Regular VCFs must be filtered either by "
        "variant recalibration (Best Practice) or hard-filtering before use in downstream analyses. If using the GVCF workflow, the "
        "output is a GVCF file that must first be run through GenotypeGVCFs and then filtering before further analysis.",
        "bam": "File to which assembled haplotypes should be written.",
    },
    name="Call germline SNPs and indels via local re-assembly of haplotypes",
    description=(
        "The HaplotypeCaller is capable of calling SNPs and indels simultaneously via local de-novo assembly of haplotypes in an active "
        "region. In other words, whenever the program encounters a region showing signs of variation, it discards the existing mapping "
        "information and completely reassembles the reads in that region. This allows the HaplotypeCaller to be more accurate when calling"
        " regions that are traditionally difficult to call, for example when they contain different types of variants close to each "
        "other. It also makes the HaplotypeCaller much better at calling indels than position-based callers like UnifiedGenotyper."
    ),
)

plugin.methods.register_function(
    function=q2_gatk.create_seq_dict,
    inputs={"reference_fasta": FeatureData[Sequence]},
    parameters={},
    outputs={"dict": FeatureData[DictFormat]},
    input_descriptions={
        "reference_fasta": ("Reference DNA sequence FASTA"),
    },
    parameter_descriptions={},
    output_descriptions={
        "dict": "The output SAM file contains a header but no SAMRecords, and the header contains only sequence records.",
    },
    name="Call germline SNPs and indels via local re-assembly of haplotypes",
    description=(
        "Creates a sequence dictionary for a reference sequence. This tool creates a sequence dictionary file (with .dict extension)"
        " from a reference sequence provided in FASTA format, which is required by many processing and analysis tools."
    ),
)

plugin.register_formats(VCFDirFormat)
plugin.register_semantic_type_to_format(FeatureData[VCFFormat], artifact_format=VCFDirFormat)

plugin.register_formats(DictDirFormat)
plugin.register_semantic_type_to_format(FeatureData[DictFormat], artifact_format=DictDirFormat)
