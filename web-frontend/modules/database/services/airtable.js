export default (client) => {
  return {
    create(groupId, shareURL, timezone) {
      return client.post(`/database/airtable/create-import-job/`, {
        group_id: groupId,
        airtable_share_url: shareURL,
        timezone,
      })
    },
    get(jobId) {
      return client.get(`/database/airtable/import-job/${jobId}/`)
    },
  }
}
