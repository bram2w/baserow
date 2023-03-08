export default (client) => {
  return {
    create(groupId, shareURL) {
      return client.post(`/jobs/`, {
        type: 'airtable',
        group_id: groupId,
        airtable_share_url: shareURL,
      })
    },
  }
}
