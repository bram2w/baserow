import { resolveColor } from '@baserow/modules/core/utils/colors'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'

export default {
  computed: {
    headingColorVariables() {
      const level = this.values?.level || this.element.level
      const variables = themeToColorVariables(this.builder.theme)
      variables.unshift({
        name: `H${level} default`,
        value: 'default',
        color: this.builder.theme[`heading_${level}_color`],
      })
      return variables
    },
  },
  methods: {
    resolveColor,
  },
}
