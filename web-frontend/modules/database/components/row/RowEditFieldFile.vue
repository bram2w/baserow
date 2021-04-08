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
            <Editable
              :ref="'rename-' + index"
              :value="file.visible_name"
              @change="renameFile(value, index, $event.value)"
            ></Editable>
          </div>
          <div class="field-file__info">
            {{ getDate(file.uploaded_at) }} - {{ file.size | formatBytes }}
          </div>
        </div>
        <div class="field-file__actions">
          <a
            v-if="!readOnly"
            v-tooltip="'rename'"
            class="field-file__action"
            @click="$refs['rename-' + index][0].edit()"
          >
            <i class="fas fa-pen"></i>
          </a>
          <a
            v-tooltip="'download'"
            target="_blank"
            :href="file.url"
            class="field-file__action"
          >
            <i class="fas fa-download"></i>
          </a>
          <a
            v-if="!readOnly"
            v-tooltip="'delete'"
            class="field-file__action"
            @click="removeFile(value, index)"
          >
            <i class="fas fa-trash"></i>
          </a>
        </div>
      </li>
    </ul>
    <a v-if="!readOnly" class="add" @click.prevent="showModal()">
      <i class="fas fa-plus add__icon"></i>
      Add a file
    </a>
    <UserFilesModal
      v-if="!readOnly"
      ref="uploadModal"
      @uploaded="addFiles(value, $event)"
    ></UserFilesModal>
    <FileFieldModal
      v-if="Boolean(value)"
      ref="fileModal"
      :files="value"
      :read-only="readOnly"
      @removed="removeFile(value, $event)"
      @renamed="renameFile(value, $event.index, $event.value)"
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
