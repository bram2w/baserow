export default (client) => {
  return {
    fetchStructure() {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashStructureView.get
       *
       * Queries the backend for the workspaces and applications that the current user can
       * see and manage trash for.
       */
      return client.get(`/trash/`)
    },
    fetchContents({
      workspaceId,
      applicationId = null,
      page = null,
      adoptWorkspace = true,
    }) {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashContentsView.get
       *
       * Queries the backend for a page of trashed items in the provided workspace or
       * application. If application is specified it must be in the workspace with the
       * id of the workspaceId parameter.
       */
      const config = {
        params: {},
      }

      if (page !== null) {
        config.params.page = page
      }

      if (adoptWorkspace === true) {
        config.params.respond_with_workspace_rename = true
      }

      if (applicationId !== null) {
        config.params.application_id = applicationId
      }

      return client.get(`/trash/workspace/${workspaceId}/`, config)
    },
    emptyContents({ workspaceId, applicationId = null }) {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashContentsView.delete
       *
       * Sends a delete request to the backend which will empty any trash items either
       * for the entire workspace is the applicationId is null. Or only trash in the
       * application if applicationId is not null. The workspaceId must match the
       * applications workspace.
       */
      const config = {
        params: {},
      }

      if (applicationId !== null) {
        config.params.application_id = applicationId
      }

      return client.delete(`/trash/workspace/${workspaceId}/`, config)
    },
    restore(restoreData) {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashItemView.patch
       *
       * Restores a trashed item. restoreData should be a dict with three keys,
       * "trash_item_type", "parent_trash_item_id" (optional when the item has no
       * parent) and "trash_item_id".
       */
      return client.patch(`/trash/restore/`, restoreData)
    },
  }
}
