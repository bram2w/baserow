class PostgresFullTextSearchDisabledException(Exception):
    """
    Raised when the Postgres full-text specific search handler methods
    are called, and `USE_PG_FULLTEXT_SEARCH` is disabled.
    """
