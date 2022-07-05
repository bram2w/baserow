export default (client) => {
  return {
    create(groupId, shareURL, timezone) {
      return client.post(`/jobs/`, {
        type: 'airtable',
        group_id: groupId,
        airtable_share_url: shareURL,
        timezone,
      })
    },
  }
}
