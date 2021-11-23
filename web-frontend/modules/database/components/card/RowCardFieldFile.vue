<template functional>
  <div class="card-file__list-wrapper">
    <ul class="card-file__list">
      <li
        v-for="(file, index) in props.value"
        :key="file.name + index"
        class="card-file__item"
      >
        <img
          v-if="file.is_image"
          class="card-file__image"
          :src="file.thumbnails.tiny.url"
        />
        <i
          v-else
          class="fas card-file__icon"
          :class="'fa-' + $options.methods.getIconClass(file.mime_type)"
        ></i>
      </li>
    </ul>
  </div>
</template>

<script>
import { mimetype2fa } from '@baserow/modules/core/utils/fontawesome'

export default {
  height: 22,
  name: 'RowCardFieldFile',
  methods: {
    getIconClass(mimeType) {
      return mimetype2fa(mimeType)
    },
  },
}
</script>
