<template>
  <div class="image_input">
    <div class="image_input__image-placeholder">
      <img class="image_input__image-placeholder-img" :src="imageUrl" />
      <a
        v-if="removable"
        class="image_input__thumbnail-remove"
        @click="$emit('input', null)"
      >
        <i class="iconoir-cancel"></i>
        {{ $t('action.remove') }}
      </a>
    </div>
    <div>
      <div class="image_input__image-upload">
        <span class="image_input__image-upload-description">
          {{ labelDescription || $t('imageInput.labelDescription') }}
        </span>
        <Button
          prepend-icon="iconoir-upload-square"
          type="primary"
          @click="openFileUploadModal"
        >
          {{ labelButton || $t('imageInput.labelButton') }}
        </Button>
      </div>
    </div>
    <UserFilesModal
      ref="userFilesModal"
      :multiple-files="multipleFiles"
      :file-types-acceptable="allowedImageTypes"
      @uploaded="fileUploaded"
    />
  </div>
</template>

<script>
import UserFilesModal from '@baserow/modules/core/components/files/UserFilesModal'
import { UploadFileUserFileUploadType } from '@baserow/modules/core/userFileUploadTypes'
import { IMAGE_FILE_TYPES } from '@baserow/modules/core/enums'

export default {
  name: 'ImageInput',
  components: {
    UserFilesModal,
  },
  props: {
    value: {
      type: Object,
      required: false,
      default: null,
    },
    allowedImageTypes: {
      type: Array,
      required: false,
      default: () => {
        return IMAGE_FILE_TYPES
      },
    },
    multipleFiles: {
      type: Boolean,
      required: false,
      default: false,
    },
    labelDescription: {
      type: String,
      required: false,
      default: '',
    },
    labelButton: {
      type: String,
      required: false,
      default: '',
    },
    defaultImage: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {}
  },
  computed: {
    imageUrl() {
      if (!this.value) {
        return this.defaultImage
      }
      return this.value.url
    },
    removable() {
      return this.value !== null
    },
  },
  methods: {
    openFileUploadModal() {
      this.$refs.userFilesModal.show(UploadFileUserFileUploadType.getType())
    },
    fileUploaded([file]) {
      this.$refs.userFilesModal.hide()
      if (file?.name) {
        this.$emit('input', file)
      }
    },
  },
}
</script>
