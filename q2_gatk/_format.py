import subprocess
import os

import qiime2.plugin.model as model
from q2_types_genomics.per_sample_data._format import BAMFormat
from qiime2.plugin import ValidationError
from pathlib import Path


class VCFFileFormat(model.TextFileFormat):
    """VCFFileFormat."""

    # TODO: Test validation by qiime tools import a VCF file
    def _validate_(self, *args):
        result = subprocess.run(["gatk", "ValidateVariants", "-V", str(self)])
        if result.returncode != 0:
            raise ValidationError("This is not a valid VCF file.")


VCFDirFormat = model.SingleFileDirectoryFormat("VCFDirFormat", "vcf.vcf", VCFFileFormat)


class DictFileFormat(model.TextFileFormat):
    """DictFileFormat."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass


DictDirFormat = model.SingleFileDirectoryFormat("DictDirFormat", "fasta.dict", DictFileFormat)


class MetricsFileFormat(model.TextFileFormat):
    """MetricsFileFormat."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass


MetricsDirFormat = model.SingleFileDirectoryFormat("MetricsDirFormat", "metrics.txt", MetricsFileFormat)


class BamIndexFileFormat(model.TextFileFormat):
    """BamIndexFileFormat."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass

#BamIndexDirFormat = model.SingleFileDirectoryFormat("BamIndexDirFormat", r'.+\.bai', BamIndexFileFormat)

#class BAMIndexDirFmt(model.DirectoryFormat):
#    bais = model.FileCollection(r'.+\.bai', format=BamIndexFileFormat)

#    @bais.set_path_maker
#    def bais_path_maker(self, sample_id):
#        return '%s.bai' % sample_id
    
class BAMIndexAlignmentDirectoryFormat(model.DirectoryFormat):
    bams = model.FileCollection(r".+\.bam",
                                    format=BAMFormat)

    bais = model.FileCollection(r".+\.bai",
                                     format=BamIndexFileFormat)
    
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
        return sorted([os.path.join(str(self.path), path) for path, _ in bound_collection.iter_views(view_type=BamIndexFileFormat)]
