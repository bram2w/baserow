import { resolveColor } from '@baserow/modules/core/utils/colors'
import { ThemeConfigBlockType } from '@baserow/modules/builder/themeConfigBlockTypes'
import form from '@baserow/modules/core/mixins/form'
import {
  DATA_PROVIDERS_ALLOWED_ELEMENTS,
  DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS,
} from '@baserow/modules/builder/enums'

export default {
  inject: ['workspace', 'builder', 'page', 'mode'],
  mixins: [form],
  computed: {
    themeConfigBlocks() {
      return this.$registry.getOrderedList('themeConfigBlock')
    },
    colorVariables() {
      return ThemeConfigBlockType.getAllColorVariables(
        this.themeConfigBlocks,
        this.builder.theme
      )
    },
    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
    DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS: () =>
      DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS,
  },
  methods: {
    resolveColor,
  },
}
