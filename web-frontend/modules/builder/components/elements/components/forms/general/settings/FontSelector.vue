<template>
  <ColorInputGroup
    v-model="values.font_color"
    :label="$t('fontSidePanelForm.label')"
    :color-variables="colorVariables"
  />
</template>

<script>
import ColorInputGroup from '@baserow/modules/core/components/ColorInputGroup'
import form from '@baserow/modules/core/mixins/form'
import { resolveColor } from '@baserow/modules/core/utils/colors'

export default {
  name: 'FontSelector',
  components: { ColorInputGroup },
  mixins: [form],
  props: {
    colorVariables: {
      type: Array,
      required: true,
    },
  },
  data() {
    return { values: { font_color: 'primary' }, allowedValues: ['font_color'] }
  },
  methods: { resolveColor },
}
</script>
