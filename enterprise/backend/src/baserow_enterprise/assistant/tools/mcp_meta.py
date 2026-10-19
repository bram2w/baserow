from dataclasses import dataclass
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


@dataclass(frozen=True)
class MCPToolMeta:
    title: str
    group: str
    read_only: bool
    destructive: bool


def mcp_tool(
    *, title: str, group: str, read_only: bool = False, destructive: bool = False
) -> Callable[[F], F]:
    """Mark a Kuma tool function for the MCP server as well."""

    if read_only and destructive:
        raise ValueError("A tool can't be both read-only and destructive.")
    meta = MCPToolMeta(title, group, read_only, destructive)

    def decorate(fn: F) -> F:
        fn.__mcp__ = meta
        return fn

    return decorate


def get_mcp_meta(fn: Callable) -> MCPToolMeta | None:
    return getattr(fn, "__mcp__", None)
