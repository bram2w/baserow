<template>
  <div class="upload-files__file-uploaded">
    <div class="field-file__preview">
      <a class="field-file__icon" @click="$emit('click')">
        <img v-if="file.is_image" :src="file.thumbnails.small.url" />
        <i v-else :class="iconClass"></i>
      </a>
    </div>
    <div class="field-file__description">
      <div class="field-file__name">
        <Editable
          ref="nameEditable"
          :value="file.visible_name"
          @change="$emit('rename', $event.value)"
        ></Editable>
      </div>
      <div class="field-file__info">
        <div>
          {{ getDate(file.uploaded_at) }} -
          {{ formatSize(file.size) }}
        </div>
      </div>
    </div>
    <div class="field-file__actions">
      <ButtonIcon
        v-if="!readOnly"
        v-tooltip="$t('action.rename')"
        size="small"
        icon="iconoir-edit-pencil"
        @click="$refs.nameEditable.edit()"
      ></ButtonIcon>
      <DownloadLink
        :filename="file.visible_name"
        :url="file.url"
        class="button-icon button-icon--small"
        loading-class="button-icon--loading"
      >
        <template #default="{ loading }">
          <i v-if="!loading" class="button-icon__icon iconoir-download" />
        </template>
      </DownloadLink>
      <ButtonIcon
        v-if="!readOnly"
        v-tooltip="$t('action.delete')"
        size="small"
        icon="iconoir-bin"
        @click="$emit('delete')"
      ></ButtonIcon>
    </div>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'FileUploaded',
  props: {
    file: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
    iconClass: {
      type: String,
      required: false,
      default: null,
    },
  },
  methods: {
    resetName() {
      this.$refs.nameEditable.set()
    },
    getDate(value) {
      return moment.utc(value).format('MMM Do YYYY [at] H:mm')
    },
    /**
     * Originally from
     * https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
     *
     * Converts an integer representing the amount of bytes to a human readable format.
     * Where for example 1024 will end up in 1KB.
     */
    formatSize(bytes) {
      if (bytes === 0) return '0 ' + this.$i18n.t(`rowEditFieldFile.sizes.0`)
      const k = 1024
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      const float = parseFloat((bytes / k ** i).toFixed(2)).toLocaleString(
        this.$i18n.locale
      )
      return float + ' ' + this.$i18n.t(`rowEditFieldFile.sizes.${i}`)
    },
  },
}
</script>
