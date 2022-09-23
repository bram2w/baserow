module.exports = {
  type: 'custom',
  test: {
    url: `{{bundle.authData.apiURL}}/api/database/tokens/check/`,
    method: 'GET',
    headers: { 'Authorization': 'Token {{bundle.authData.apiToken}}' },
  },
  fields: [
    {
      computed: false,
      key: 'apiToken',
      required: true,
      label: 'Baserow API token',
      type: 'string',
      helpText:
        'Please enter your Baserow API token. Can be found by clicking on your ' +
        'account in the top left corner -> Settings -> API tokens.'
    },
    {
      computed: false,
      key: 'apiURL',
      required: false,
      label: 'Baserow API URL',
      default: 'https://api.baserow.io',
      type: 'string',
      helpText:
        'Please enter your Baserow API URL. If you are using baserow.io, you ' +
        'can leave the default one.'
    },
  ],
  connectionLabel: 'Baserow API authentication',
  customConfig: {}
}
