<template functional>
  <div
    v-tooltip="props.selected ? props.value.visible_name : null"
    class="array-field__file"
  >
    <a
      class="array-field__file-link"
      @click.prevent="$options.methods.onClick(listeners, props)"
    >
      <img
        v-if="props.value.is_image"
        class="array-field__file-image"
        :src="props.value.thumbnails?.tiny?.url"
      />
      <i
        v-else
        class="array-field__file-icon"
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
