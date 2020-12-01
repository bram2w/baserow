<template>
  <div class="control__elements">
    <ul class="field-file__list">
      <li
        v-for="(file, index) in value"
        :key="file.name + '-' + index"
        class="field-file__item"
      >
        <div class="field-file__preview">
          <a class="field-file__icon" @click="$refs.fileModal.show(index)">
            <img v-if="file.is_image" :src="file.thumbnails.small.url" />
            <i
              v-else
              class="fas"
              :class="'fa-' + getIconClass(file.mime_type)"
            ></i>
          </a>
        </div>
        <div class="field-file__description">
          <div class="field-file__name">
            {{ file.visible_name }}
          </div>
          <div class="field-file__info">
            {{ getDate(file.uploaded_at) }} - {{ file.size | formatBytes }}
          </div>
        </div>
        <div class="field-file__actions">
          <a
            v-tooltip="'download'"
            target="_blank"
            :href="file.url"
            class="field-file__action"
          >
            <i class="fas fa-download"></i>
          </a>
          <a
            v-tooltip="'delete'"
            class="field-file__action"
            @click="removeFile(value, index)"
          >
            <i class="fas fa-trash"></i>
          </a>
        </div>
      </li>
    </ul>
    <a class="field-file__add" @click.prevent="showModal()">
      <i class="fas fa-plus field-file__add-icon"></i>
      Add a file
    </a>
    <UserFilesModal
      ref="uploadModal"
      @uploaded="addFiles(value, $event)"
    ></UserFilesModal>
    <FileFieldModal
      ref="fileModal"
      :files="value"
      @removed="removeFile(value, $event)"
    ></FileFieldModal>
  </div>
</template>

<script>
import moment from 'moment'

import { UploadFileUserFileUploadType } from '@baserow/modules/core/userFileUploadTypes'
import UserFilesModal from '@baserow/modules/core/components/files/UserFilesModal'
import FileFieldModal from '@baserow/modules/database/components/field/FileFieldModal'
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import fileField from '@baserow/modules/database/mixins/fileField'

export default {
  components: { UserFilesModal, FileFieldModal },
  mixins: [rowEditField, fileField],
  methods: {
    showModal() {
      this.$refs.uploadModal.show(UploadFileUserFileUploadType.getType())
    },
    getDate(value) {
      return moment.utc(value).format('MMM Do YYYY [at] H:mm')
    },
  },
}
</script>
