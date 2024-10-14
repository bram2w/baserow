from typing import TypedDict


class DashboardDict(TypedDict):
    id: int
    name: str
    description: str
    order: int
    type: str
