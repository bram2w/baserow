<template>
  <div class="ab-tag-group">
    <div
      v-for="(tag, index) in tags"
      :key="`${index}-${tag.value}`"
      class="ab-tag"
      :style="`background-color: ${resolveColor(tag.color, colorVariables)}`"
    >
      {{ tag.value }}
    </div>
  </div>
</template>

<script>
import { resolveColor } from '@baserow/modules/core/utils/colors'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'

export default {
  name: 'TagsField',
  inject: ['builder'],
  props: {
    tags: {
      type: Array,
      required: true,
      default: () => [],
    },
  },
  computed: {
    colorVariables() {
      return themeToColorVariables(this.builder.theme)
    },
  },
  methods: { resolveColor },
}
</script>
