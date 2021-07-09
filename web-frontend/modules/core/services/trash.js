export default (client) => {
  return {
    fetchStructure() {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashStructureView.get
       *
       * Queries the backend for the groups and applications that the current user can
       * see and manage trash for.
       */
      return client.get(`/trash/`)
    },
    fetchContents({ groupId, applicationId = null, page = null }) {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashContentsView.get
       *
       * Queries the backend for a page of trashed items in the provided group or
       * application. If application is specified it must be in the group with the
       * id of the groupId parameter.
       */
      const config = {
        params: {},
      }

      if (page !== null) {
        config.params.page = page
      }

      if (applicationId !== null) {
        config.params.application_id = applicationId
      }

      return client.get(`/trash/group/${groupId}/`, config)
    },
    emptyContents({ groupId, applicationId = null }) {
      /**
       * Corresponding Backend View: baserow.api.trash.views.TrashContentsView.delete
       *
       * Sends a delete request to the backend which will empty any trash items either
       * for the entire group is the applicationId is null. Or only trash in the
       * application if applicationId is not null. The groupId must match the
       * applications group.
       */
      const config = {
        params: {},
      }

      if (applicationId !== null) {
        config.params.application_id = applicationId
      }

      return client.delete(`/trash/group/${groupId}/`, config)
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
