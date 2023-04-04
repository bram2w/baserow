# API deprecations

Baserow may, from time to time, deprecate functionality in its REST and/or Websocket 
API. To ensure that your application runs smoothly, and without downtime, we will use this
page to inform API integrators of what features are deprecated, and how long we'll
support compatibility for.

## Groups: renamed to Workspace

### Summary

In early 2023 [we decided](https://gitlab.com/bramw/baserow/-/issues/1303) to rename 
the concept of a "group" to "workspace".

For nearly all users, the only noticeable change will be that within the UI, references
to "group" will disappear in favor of "workspace".

For API consumers, however, they will need to eventually migrate from our "group"
endpoints to functionally identical "workspace" ones. To help API consumers migrate to
the new endpoints, our [API specification](https://api.baserow.io/api/redoc/) has been
updated so that each deprecated "group" endpoint will suggest the functionally identical
"workspace" equivalent.

## REST API changes

The most significant change to our API is that we've duplicated all "group"
endpoints so that there is a functionally identical "workspace" one.

For example, the [`create_group`](https://api.baserow.io/api/redoc/#tag/Groups/operation/create_group)
endpoint (which is now marked as deprecated) has a functionally identical
[`create_workspace`](https://api.baserow.io/api/redoc/#tag/Workspaces/operation/list_workspaces) endpoint.

In any API or WebSocket response which previously serialized a "group" ID, name or
nested object, there will be an identical "workspace" one.

This means that there will be no intentional breaking changes in our API responses.
There are, however, some codebase changes to be aware of.

## Minor changes

- The directory `baserow.api.groups` has been renamed to `baserow.api.workspaces`.
- The directory `baserow_premium.admin.groups` has been renamed to `baserow_premium`.
  `admin.workspaces`.

## Major changes

- All "group" endpoints now have a corresponding "workspace" endpoint.
- All "group" endpoint views have been moved to a [`compat` directory](https://gitlab.com/bramw/baserow/-/tree/develop/backend/src/baserow/compat).

## Non-REST API breaking changes

- The command `fill_group` was renamed to `fill_workspace`.
- The command `import_group_applications` was renamed to `import_workspace_applications`.
- The command `export_group_applications` was renamed to
  `export_workspace_applications`.

### Migration timeline

- **Early 2023**: the "group" endpoints will be marked as deprecated. All endpoints 
  which currently return a `group` ID, name or nested object, will keep returning 
  them. The only change to these responses will be the inclusion of an exact 
  `workspace` copy.
- **In the remainder of 2023**: Baserow will, every few months, periodically remind API 
  consumers that they need to move from the "group" endpoints to the "workspace" ones.
- **Early 2024**: the "group" endpoints will be removed, and the "workspace" endpoints 
  will be required.
