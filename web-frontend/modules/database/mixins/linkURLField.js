import { isValidURL } from '@baserow/modules/core/utils/string'

export default {
  methods: {
    isValid(value) {
      return isValidURL(value?.url)
    },
    getLabelOrURL(value) {
      if (!value) {
        return ''
      } else {
        return value.label ? value.label : value.url
      }
    },
  },
}
