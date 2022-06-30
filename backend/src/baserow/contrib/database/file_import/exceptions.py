class FileImportMaxErrorCountExceeded(Exception):
    """
    Raised when a file import job raise too many error.
    """

    def __init__(self, report, *args, **kwargs):
        self.report = report
        super().__init__("Too many errors", *args, **kwargs)
