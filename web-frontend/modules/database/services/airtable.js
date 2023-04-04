export default (client) => {
  return {
    create(workspaceId, shareURL) {
      return client.post(`/jobs/`, {
        type: 'airtable',
        workspace_id: workspaceId,
        airtable_share_url: shareURL,
      })
    },
  }
}
