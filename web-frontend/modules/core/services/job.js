export default (client) => {
  return {
    create(jobType, params = {}) {
      return client.post(`/jobs/`, {
        type: jobType,
        ...params,
      })
    },
    get(jobId) {
      return client.get(`/jobs/${jobId}/`)
    },
  }
}
