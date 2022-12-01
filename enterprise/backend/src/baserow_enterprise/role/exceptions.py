class CantLowerAdminsRoleOnChildException(Exception):
    """
    Raised when the user tries to assign a role to scope that has already the ADMIN
    computed role.
    """
