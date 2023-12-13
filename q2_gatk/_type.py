from q2_types.feature_data import FeatureData
from qiime2.plugin import SemanticType

Variants = SemanticType("VariantType", variant_of=FeatureData.field["type"])


Metrics = SemanticType("MetricsType", variant_of=FeatureData.field["type"])

#BamIndexFormat = SemanticType("BamIndexFormat", variant_of=FeatureData.field["type"])

BAMIndexAlignment = SemanticType("BAMIndexAlignmentType", variant_of=FeatureData.field["type"])