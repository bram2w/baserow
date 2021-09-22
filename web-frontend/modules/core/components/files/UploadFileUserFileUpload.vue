<template>
  <div>
    <h2 class="box__title">{{ $t('uploadFileUserFileUpload.title') }}</h2>
    <input
      v-show="false"
      ref="file"
      type="file"
      multiple
      @change="addFile($event)"
    />
    <div
      class="upload-files__dropzone"
      :class="{ 'upload-files__dropzone--dragging': dragging }"
      @click.prevent="$refs.file.click($event)"
      @drop.prevent="addFile($event)"
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
    <ul v-show="files.length > 0" class="upload-files__list">
      <li v-for="file in files" :key="file.id" class="upload-files__item">
        <div class="upload-files__preview">
          <div class="upload-files__icon">
            <i
              v-if="!file.isImage"
              class="fas"
              :class="'fa-' + file.iconClass"
            ></i>
            <img v-if="file.isImage" :ref="'file-image-' + file.id" />
          </div>
        </div>
        <div class="upload-files__description">
          <div class="upload-files__name">
            {{ file.file.name }}
            <div class="upload-files__percentage">{{ file.percentage }}%</div>
          </div>
          <div v-if="file.state === 'failed'" class="upload-files__error">
            {{ file.error }}
          </div>
          <div v-else class="upload-files__progress">
            <div
              class="upload-files__progress-bar"
              :class="{
                'upload-files__progress-bar--finished':
                  file.state === 'finished',
              }"
              :style="{ width: file.percentage + '%' }"
            ></div>
          </div>
        </div>
        <div class="upload-files__state">
          <i
            v-show="file.state === 'finished'"
            class="upload-files__state-waiting fas fa-check"
          ></i>
          <i
            v-show="file.state === 'failed'"
            class="upload-files__state-failed fas fa-times"
          ></i>
          <div
            v-show="file.state === 'uploading'"
            class="upload-files__state-loading loading"
          ></div>
          <a
            v-show="file.state === 'waiting'"
            class="upload-files__state-link"
            @click.prevent="removeFile(file.id)"
          >
            <i class="fas fa-trash"></i>
          </a>
        </div>
      </li>
    </ul>
    <div v-show="files.length > 0" class="align-right">
      <a
        class="button button--large"
        :class="{ 'button--loading': uploading }"
        :disabled="uploading"
        @click="upload()"
      >
        <template v-if="!uploading && hasFailed">{{
          $t('uploadFileUserFileUpload.retry')
        }}</template>
        <template v-else>{{ $t('action.upload') }}</template>
      </a>
    </div>
  </div>
</template>

<script>
import { uuid } from '@baserow/modules/core/utils/string'
import { mimetype2fa } from '@baserow/modules/core/utils/fontawesome'
import { generateThumbnail } from '@baserow/modules/core/utils/image'
import UserFileService from '@baserow/modules/core/services/userFile'

export default {
  name: 'UploadFileUserFileUpload',
  data() {
    return {
      uploading: false,
      dragging: false,
      files: [],
      responses: [],
    }
  },
  computed: {
    hasFailed() {
      for (let i = 0; i < this.files.length; i++) {
        if (this.files[i].state === 'failed') {
          return true
        }
      }
      return false
    },
  },
  methods: {
    /**
     * Called when new files must be added to the overview. It can handle files via a
     * drop event, but also via a file upload input event.
     */
    addFile(event) {
      this.dragging = false

      let files = null

      if (event.target.files) {
        // Files via the file upload input.
        files = event.target.files
      } else if (event.dataTransfer) {
        // Files via drag and drop.
        files = event.dataTransfer.files
      }

      if (files === null) {
        return
      }

      const imageTypes = ['image/jpeg', 'image/jpg', 'image/png']

      Array.from(files).forEach((file) => {
        const isImage = imageTypes.includes(file.type)
        const item = {
          id: uuid(),
          percentage: 0,
          error: null,
          state: 'waiting',
          iconClass: mimetype2fa(file.type),
          isImage,
          file,
        }

        this.files.push(item)

        // If the file is an image we can generate a preview thumbnail after the img
        // element has been rendered.
        if (isImage) {
          this.$nextTick(() => {
            this.generateThumbnail(item)
          })
        }
      })
    },
    /**
     * Generates and sets a thumbnail of the just chosen file.
     */
    generateThumbnail(item) {
      const reader = new FileReader()
      reader.onload = async () => {
        const dataUrl = await generateThumbnail(reader.result, 48, 48)
        this.$refs['file-image-' + item.id][0].src = dataUrl
      }
      reader.readAsDataURL(item.file)
    },
    removeFile(id) {
      const index = this.files.findIndex((file) => file.id === id)

      if (index === -1) {
        return
      }

      this.files.splice(index, 1)
    },
    upload() {
      // The upload button, which calls this method, could also be the retry button. In
      // that case the failed files must be converted to waiting.
      this.files.forEach((file) => {
        if (file.state === 'failed') {
          file.state = 'waiting'
          file.error = null
          file.percentage = 0
        }
      })

      this.uploadNext()
    },
    /**
     * Is called when the next file must be uploaded. If there aren't any waiting ones
     * and at least one file has been uploaded successfully the uploaded event is
     * emitted.
     */
    async uploadNext() {
      this.uploading = true

      const file = this.files.find((file) => file.state === 'waiting')

      // If no waiting files have been found we can assume the upload progress is
      // completed.
      if (file === undefined) {
        this.uploading = false

        // If at least one of the files has been uploaded successfully we can
        // communicate the responses to the parent component.
        if (this.responses.length > 0) {
          this.$emit('uploaded', this.responses)
        }

        return
      }

      const progress = (event) => {
        const percentage = Math.round((event.loaded * 100) / event.total)
        file.percentage = percentage
      }

      file.state = 'uploading'

      try {
        const { data } = await UserFileService(this.$client).uploadFile(
          file.file,
          progress
        )
        this.responses.push(data)
        file.state = 'finished'
      } catch (error) {
        const message = error.handler.getMessage('userFile')
        error.handler.handled()
        file.state = 'failed'
        file.error = message.message
      }

      this.uploadNext()
    },
  },
}
</script>

<i18n>
{
  "en": {
    "uploadFileUserFileUpload": {
      "title": "Upload from my device",
      "drop": "Drop here",
      "clickOrDrop": "Click or drop your files here",
      "retry": "Retry"
    }
  },
  "fr": {
    "uploadFileUserFileUpload": {
      "title": "Envoyer un fichier",
      "drop": "Déposez ici",
      "clickOrDrop": "Cliquez ou déposez votre fichier ici",
      "retry": "Recommencer"
    }
  }
}
</i18n>
