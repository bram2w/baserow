export default (client) => {
  return {
    list(applicationId) {
      return client.get(`/snapshots/application/${applicationId}/`)
    },
    create(applicationId, values) {
      return client.post(`/snapshots/application/${applicationId}/`, values)
    },
    restore(snapshotId) {
      return client.post(`/snapshots/${snapshotId}/restore/`)
    },
    delete(snapshotId) {
      return client.delete(`/snapshots/${snapshotId}/`)
    },
  }
}
