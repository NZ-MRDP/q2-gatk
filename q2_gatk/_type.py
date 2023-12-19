from q2_types.feature_data import FeatureData
from qiime2.plugin import SemanticType

Variants = SemanticType("Variants", variant_of=FeatureData.field["type"])


Metrics = SemanticType("Metrics", variant_of=FeatureData.field["type"])

#BamIndexFormat = SemanticType("BamIndexFormat", variant_of=FeatureData.field["type"])

BAMIndexAlignment = SemanticType("BAMIndexAlignment", variant_of=FeatureData.field["type"])