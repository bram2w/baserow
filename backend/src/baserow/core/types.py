from typing import Any, NamedTuple, Optional, TypedDict

# A scope object needs to have a related registered ScopeObjectType
ScopeObject = Any

# A context object can be any object
ContextObject = Any

# A subject needs to have a related registered SubjectType
Subject = Any


# An actor is an object that can do an operation. For now only AbstractUser or Token
Actor = Any


class PermissionCheck(NamedTuple):
    actor: Actor
    operation_name: str
    context: Optional[ContextObject] = None


class PermissionObjectResult(TypedDict):
    name: str
    permissions: Any
