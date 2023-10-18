import form from '@baserow/modules/core/mixins/form'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'

export default {
  mixins: [form],
  computed: {
    dataProvidersAllowed() {
      return DATA_PROVIDERS_ALLOWED_ELEMENTS
    },
  },
}
