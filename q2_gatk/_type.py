from q2_types.feature_data import FeatureData
from qiime2.plugin import SemanticType

VCFFormat = SemanticType("VCFFormat", variant_of=FeatureData.field["type"])
