import addPublicAuthTokenHeader from '@baserow/modules/database/utils/publicView'

export default (client) => {
  const prepareRequestConfig = ({ publicAuthToken = null }) => {
    const config = { headers: {} }
    if (publicAuthToken) {
      addPublicAuthTokenHeader(config, publicAuthToken)
    }
    return config
  }

  return {
    getMetaInformation(slug, publicAuthToken = null) {
      const config = prepareRequestConfig({ publicAuthToken })
      return client.get(`/database/views/form/${slug}/submit/`, config)
    },
    submit(slug, values, publicAuthToken = null) {
      const config = prepareRequestConfig({ publicAuthToken })
      return client.post(`/database/views/form/${slug}/submit/`, values, config)
    },
  }
}
