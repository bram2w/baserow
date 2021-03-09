<template functional>
  <div
    class="grid-view__cell grid-field-file__cell"
    @drop.prevent="$options.methods.drop(parent, props, $event)"
    @dragover.prevent
    @dragenter.prevent="$options.methods.dragEnter(parent, props, $event)"
    @dragleave="$options.methods.dragLeave(parent, props, $event)"
  >
    <div
      v-show="Object.prototype.hasOwnProperty.call(props.state, props.field.id)"
      class="grid-field-file__dragging"
    >
      <div>
        <i class="grid-field-file__drop-icon fas fa-cloud-upload-alt"></i>
        Drop here
      </div>
    </div>
    <ul v-if="Array.isArray(props.value)" class="grid-field-file__list">
      <li
        v-for="(file, index) in props.value"
        :key="file.name + index"
        class="grid-field-file__item"
      >
        <a class="grid-field-file__link">
          <img
            v-if="file.is_image"
            class="grid-field-file__image"
            :src="file.thumbnails.tiny.url"
          />
          <i
            v-else
            class="fas grid-field-file__icon"
            :class="'fa-' + $options.methods.getIconClass(file.mime_type)"
          ></i>
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
import { mimetype2fa } from '@baserow/modules/core/utils/fontawesome'

export default {
  name: 'FunctionalGridViewFieldFile',
  methods: {
    getIconClass(mimeType) {
      return mimetype2fa(mimeType)
    },
    drop(parent, props, event) {
      if (props.readOnly) {
        return
      }

      parent.selectCell(props.field.id)
      parent.setState({})
      parent.$nextTick(() => {
        parent.$refs.selectedField.uploadFiles(event)
      })
    },
    dragEnter(parent, props, event) {
      if (props.readOnly) {
        return
      }

      parent.setState({
        [props.field.id]: event.target,
      })
    },
    dragLeave(parent, props, event) {
      if (props.readOnly) {
        return
      }

      if (
        Object.prototype.hasOwnProperty.call(props.state, props.field.id) &&
        props.state[props.field.id] === event.target
      ) {
        event.stopPropagation()
        event.preventDefault()
        parent.setState({})
      }
    },
  },
}
</script>
