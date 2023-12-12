from q2_types.feature_data import FeatureData
from qiime2.plugin import SemanticType

VariantType = SemanticType("VariantType", variant_of=FeatureData.field["type"])


MetricsType = SemanticType("MetricsType", variant_of=FeatureData.field["type"])

#BamIndexFormat = SemanticType("BamIndexFormat", variant_of=FeatureData.field["type"])

BAMIndexAlignmentType = SemanticType("BAMIndexAlignmentType", variant_of=FeatureData.field["type"])