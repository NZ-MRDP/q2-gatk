import qiime2.plugin.model as model


class VCFFileFormat(model.TextFileFormat):
    """VCFFileFormat."""

    # TODO: Add validation
    def _validate_(self, *args):
        pass


VCFDirFormat = model.SingleFileDirectoryFormat("VCFDirFormat", VCFFileFormat)
