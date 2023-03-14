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

### Breaking changes

1. The command `import_group_applications` was renamed to `import_workspace_applications`.
2. The command `export_group_applications` was renamed to `export_workspace_applications`. 
Additionally, the filename it creates is now `workspace_{id}`.
3. The command `fill_group` was renamed to `fill_workspace`.

### Migration timeline

- **Early 2023**: the "group" endpoints will be marked as deprecated. All endpoints 
  which currently return a `group` ID, name or nested object, will keep returning 
  them. The only change to these responses will be the inclusion of an exact 
  `workspace` copy.
- **In the remainder of 2023**: Baserow will, every few months, periodically remind API 
  consumers that they need to move from the "group" endpoints to the "workspace" ones.
- **Early 2024**: the "group" endpoints will be removed, and the "workspace" endpoints 
  will be required.
