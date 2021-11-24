export default (client) => {
  return {
    fetchAll() {
      return client.get('/licenses/')
    },
    fetch(id) {
      return client.get(`/licenses/${id}/`)
    },
    disconnect(id) {
      return client.delete(`/licenses/${id}/`)
    },
    register(license) {
      return client.post(`/licenses/`, { license })
    },
    lookupUsers(licenseId, page, search) {
      const config = {
        params: {
          page,
          size: 100,
        },
      }

      if (search !== null) {
        config.params.search = search
      }

      return client.get(`/licenses/${licenseId}/lookup-users/`, config)
    },
    addUser(licenseId, userId) {
      return client.post(`/licenses/${licenseId}/${userId}/`)
    },
    removeUser(licenseId, userId) {
      return client.delete(`/licenses/${licenseId}/${userId}/`)
    },
    fillSeats(licenseId) {
      return client.post(`/licenses/${licenseId}/fill-seats/`)
    },
    removeAllUsers(licenseId) {
      return client.post(`/licenses/${licenseId}/remove-all-users/`)
    },
    check(licenseId) {
      return client.get(`/licenses/${licenseId}/check/`)
    },
  }
}
