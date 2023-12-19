import os
import subprocess
from pathlib import Path

import qiime2.plugin.model as model
from q2_types_genomics.per_sample_data._format import BAMFormat
from qiime2.plugin import ValidationError


class VCFFile(model.TextFileFormat):
    """VCFFile."""

    # TODO: Test validation by qiime tools import a VCF file
    def _validate_(self, *args):
        result = subprocess.run(["gatk", "ValidateVariants", "-V", str(self)])
        if result.returncode != 0:
            raise ValidationError("This is not a valid VCF file.")
        
class VCFIndexFile(model.TextFileFormat):
    """VCFIndexFile."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass

class VCFIndexDirectory(model.DirectoryFormat):
    vcf = model.FileCollection(r".+\.vcf",
                                    format=VCFFile)

    vcf_index = model.FileCollection(r".+\.vcf.idx",
                                     format=VCFIndexFile)
    @vcf.set_path_maker
    def vcf_path_maker(self, sample_id):
        return '%s.vcf' % sample_id
    
    @vcf_index.set_path_maker
    def vcf_index_path_maker(self, sample_id):
        return '%s.vcf.idx' % sample_id


class MetricsFile(model.TextFileFormat):
    """MetricsFile."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass


MetricsDir = model.SingleFileDirectoryFormat("MetricsDir", "metrics.txt", MetricsFile)


class BamIndexFile(model.TextFileFormat):
    """BamIndexFile."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass
    
class BAMIndexAlignmentDirectory(model.DirectoryFormat):
    bams = model.FileCollection(r".+\.bam",
                                    format=BAMFormat)

    bais = model.FileCollection(r".+\.bai",
                                     format=BamIndexFile)
    
    def _validate(self, *args):
        for bam, bai in zip(self.bam_file_paths, self.bai_file_paths):
            if Path(bam).stem != Path(bai).stem:
                raise ValidationError("""Found mismatches in file names. 
                                      Bam and bai files must have matching file names before extension""")

    @bams.set_path_maker
    def bam_path_maker(self, sample_id):
        return '%s.bam' % sample_id
    
    @bais.set_path_maker
    def bai_path_maker(self, sample_id):
        return '%s.bai' % sample_id
    
    @property
    def bam_file_paths(self):
        bound_collection = model.directory_format.BoundFileCollection(self.bams, self, path_maker=self.bam_path_maker)
        return sorted([os.path.join(str(self.path), path) for path, _ in bound_collection.iter_views(view_type=BAMFormat)])
    
    @property
    def bai_file_paths(self):
        bound_collection = model.directory_format.BoundFileCollection(self.bais, self, path_maker=self.bai_path_maker)
        return sorted([os.path.join(str(self.path), path) for path, _ in bound_collection.iter_views(view_type=BamIndexFile)])
