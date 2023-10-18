export default (client) => {
  return {
    create(pageId, workflowActionType, eventType, configuration = null) {
      const payload = {
        type: workflowActionType,
        event: eventType,
        ...configuration,
      }

      return client.post(`builder/page/${pageId}/workflow_actions/`, payload)
    },
    fetchAll(pageId) {
      return client.get(`builder/page/${pageId}/workflow_actions/`)
    },
    delete(workflowActionId) {
      return client.delete(`builder/workflow_action/${workflowActionId}/`)
    },
    update(workflowActionId, values) {
      return client.patch(
        `builder/workflow_action/${workflowActionId}/`,
        values
      )
    },
  }
}
