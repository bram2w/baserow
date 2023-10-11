<template functional>
  <div class="grid-field-file__item">
    <a
      class="grid-field-file__link"
      @click.prevent="$options.methods.onClick(listeners, props)"
    >
      <img
        v-if="props.value.is_image"
        class="grid-field-file__image"
        :src="props.value.thumbnails?.tiny?.url"
      />
      <i
        v-else
        class="grid-field-file__icon"
        :class="$options.methods.getIconClass(props.value.mime_type)"
      ></i>
    </a>
  </div>
</template>

<script>
import { mimetype2icon } from '@baserow/modules/core/utils/fileTypeToIcon'

export default {
  name: 'FunctionalFormulaFileArrayItem',
  methods: {
    getIconClass(mimeType) {
      return mimetype2icon(mimeType)
    },
    onClick(listeners, props) {
      if (listeners.show) {
        listeners.show(props?.index)
      }
    },
  },
}
</script>
