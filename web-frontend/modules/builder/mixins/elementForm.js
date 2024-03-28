import { resolveColor } from '@baserow/modules/core/utils/colors'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'
import form from '@baserow/modules/core/mixins/form'
import {
  DATA_PROVIDERS_ALLOWED_ELEMENTS,
  DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS,
} from '@baserow/modules/builder/enums'

export default {
  inject: ['builder', 'page', 'mode'],
  mixins: [form],
  computed: {
    colorVariables() {
      return themeToColorVariables(this.builder.theme)
    },

    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
    DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS: () =>
      DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS,
  },
  methods: {
    resolveColor,
  },
}
