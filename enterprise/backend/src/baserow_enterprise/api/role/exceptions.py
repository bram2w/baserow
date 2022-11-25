class DuplicateRoleAssignments(Exception):
    """
    Raised when somebody tries to submit duplicate role assignments in a batch request
    """

    def __init__(self, indexes):
        super().__init__()
        self.indexes = indexes
