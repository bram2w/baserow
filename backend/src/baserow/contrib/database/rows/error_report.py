from typing import Any, Dict, List, Tuple, TypeVar

from django.conf import settings

from .exceptions import ReportMaxErrorCountExceeded

RowIndex = TypeVar("RowIndex", bound=int)


class RowErrorReport:
    def __init__(
        self,
        rows: List[Dict[str, Any]],
        error_limit: int = settings.BASEROW_MAX_ROW_REPORT_ERROR_COUNT,
    ):
        """
        The RowErrorReport is a helper to track rows errors and generate a report at
        the end.

        :param rows: the rows list.
        :param error_limit: if the error limit is exceeded, an exception is raised.
        """

        self._indexed_rows = {
            index: {"row": row, "error": None} for index, row in enumerate(rows)
        }
        self._rows = rows
        self.error_count = 0
        self.error_limit = error_limit

    def add_error(self, row_index: RowIndex, error: Dict[str, Any]):
        """
        Adds an error to the report if the error is truthy.

        :raise ReportMaxErrorCountExceeded: if the maximum error limit is exceeded.
        """

        if not error:
            return

        self.error_count += 1
        if self.error_count > self.error_limit:
            raise ReportMaxErrorCountExceeded(self.to_dict())

        self._indexed_rows[row_index]["error"] = error

    def update_row(self, row_index: RowIndex, new_row: Dict[str, Any]):
        self._indexed_rows[row_index]["row"] = new_row

    def get_valid_rows_and_mapping(
        self,
    ) -> Tuple[List[Dict[str, Any]], Dict[RowIndex, RowIndex]]:
        """
        Returns rows without error and the corresponding mapping for
        new original -> original index
        """

        valid_rows = []
        mapping = {}
        for index, _ in enumerate(self._rows):
            if not self._indexed_rows[index]["error"]:
                mapping[len(valid_rows)] = index
                valid_rows.append(self._indexed_rows[index]["row"])
        return valid_rows, mapping

    def to_dict(self) -> Dict[RowIndex, Dict[str, Any]]:
        """
        Generates the report as a dict.
        """

        report = {}
        for index, _ in enumerate(self._rows):
            if self._indexed_rows[index]["error"]:
                report[index] = self._indexed_rows[index]["error"]
        return report
