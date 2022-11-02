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
    fetchAll(filters = {}) {
      const { states, jobIds } = filters
      const params = new URLSearchParams()
      if (states !== undefined) {
        params.append('states', Array.isArray(states) ? states : [states])
      }
      if (jobIds !== undefined) {
        params.append('job_ids', jobIds)
      }
      const config = { params }
      return client.get(`/jobs/`, config)
    },
  }
}
