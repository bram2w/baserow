export default (client) => {
  return {
    getAgent(applicationId) {
      return client.get(`agent_application/${applicationId}/agent/`)
    },
    updateAgent(agentId, values) {
      return client.patch(`agent_application/agents/${agentId}/`, values)
    },
    getChats(applicationId, { limit = 50, offset = 0, origin = null } = {}) {
      const params = { limit, offset }
      if (origin) {
        params.origin = origin
      }
      return client.get(`agent_application/${applicationId}/chats/`, {
        params,
      })
    },
    getChatMessages(applicationId, chatUuid) {
      return client.get(
        `agent_application/${applicationId}/chats/${chatUuid}/messages/`
      )
    },
    sendMessage(
      applicationId,
      chatUuid,
      content,
      userFiles = [],
      { private: isPrivate = false } = {}
    ) {
      const body = { content }
      if (isPrivate) {
        body.private = true
      }
      if (userFiles.length > 0) {
        body.user_files = userFiles.map((userFile) => ({ name: userFile.name }))
      }
      return client.post(
        `agent_application/${applicationId}/chats/${chatUuid}/messages/`,
        body
      )
    },
    retryChat(chatUuid) {
      return client.post(`agent_application/chats/${chatUuid}/retry/`)
    },
    cancelChat(chatUuid) {
      return client.post(`agent_application/chats/${chatUuid}/cancel/`)
    },
    decideApprovals(chatUuid, decisions) {
      return client.post(`agent_application/chats/${chatUuid}/approvals/`, {
        decisions,
      })
    },
    updateChat(chatUuid, values) {
      return client.patch(`agent_application/chats/${chatUuid}/`, values)
    },

    draftInstructions(workspaceId, values) {
      return client.post(
        `agent_application/workspace/${workspaceId}/instructions/draft/`,
        values
      )
    },
    improveInstructions(agentId, values) {
      return client.post(
        `agent_application/agents/${agentId}/instructions/improve/`,
        values
      )
    },
    getPendingApprovals(applicationId) {
      return client.get(`agent_application/${applicationId}/approvals/`)
    },
    deleteChat(chatUuid) {
      return client.delete(`agent_application/chats/${chatUuid}/`)
    },
    getTriggers(applicationId) {
      return client.get(`agent_application/${applicationId}/triggers/`)
    },
    createTrigger(applicationId, values) {
      return client.post(`agent_application/${applicationId}/triggers/`, values)
    },
    updateTrigger(triggerId, values) {
      return client.patch(`agent_application/triggers/${triggerId}/`, values)
    },
    deleteTrigger(triggerId) {
      return client.delete(`agent_application/triggers/${triggerId}/`)
    },
    getTools(applicationId) {
      return client.get(`agent_application/${applicationId}/tools/`)
    },
    getWorkspaceTools(applicationId) {
      return client.get(`agent_application/${applicationId}/workspace_tools/`)
    },
    createTool(applicationId, values) {
      return client.post(`agent_application/${applicationId}/tools/`, values)
    },
    updateTool(toolId, values) {
      return client.patch(`agent_application/tools/${toolId}/`, values)
    },
    deleteTool(toolId) {
      return client.delete(`agent_application/tools/${toolId}/`)
    },
    getChannels(applicationId) {
      return client.get(`agent_application/${applicationId}/channels/`)
    },
    createChannel(applicationId, values) {
      return client.post(`agent_application/${applicationId}/channels/`, values)
    },
    updateChannel(channelId, values) {
      return client.patch(`agent_application/channels/${channelId}/`, values)
    },
    rotateChannelSlug(channelId) {
      return client.post(
        `/agent_application/channels/${channelId}/rotate-slug/`
      )
    },
    deleteChannel(channelId) {
      return client.delete(`agent_application/channels/${channelId}/`)
    },
  }
}
