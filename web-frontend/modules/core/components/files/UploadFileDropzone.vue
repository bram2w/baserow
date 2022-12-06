<template>
  <div>
    <input
      v-show="false"
      ref="file"
      type="file"
      multiple
      @change="$emit('input', $event)"
    />
    <div
      class="upload-files__dropzone"
      :class="{ 'upload-files__dropzone--dragging': dragging }"
      @click.prevent="$refs.file.click($event)"
      @drop.prevent="onDrop($event)"
      @dragover.prevent
      @dragenter.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
    >
      <div class="upload-files__dropzone-content">
        <i class="upload-files__dropzone-icon fas fa-cloud-upload-alt"></i>
        <div class="upload-files__dropzone-text">
          <template v-if="dragging"
            >{{ $t('uploadFileUserFileUpload.drop') }}
          </template>
          <template v-else>{{
            $t('uploadFileUserFileUpload.clickOrDrop')
          }}</template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UploadFileDropzone',
  data() {
    return {
      dragging: false,
    }
  },
  methods: {
    onDrop(event) {
      this.dragging = false
      this.$emit('input', event)
    },
  },
}
</script>
