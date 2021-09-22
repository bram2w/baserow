<template>
  <Modal :left-sidebar="true" @hidden="$emit('hidden')">
    <template #sidebar>
      <div class="modal-sidebar__head">
        <div class="modal-sidebar__head-name">
          {{ $t('userFilesModal.title') }}
        </div>
      </div>
      <ul class="modal-sidebar__nav">
        <li v-for="upload in registeredUserFileUploads" :key="upload.type">
          <a
            class="modal-sidebar__nav-link"
            :class="{ active: page === upload.type }"
            @click="setPage(upload.type)"
          >
            <i
              class="fas modal-sidebar__nav-icon"
              :class="'fa-' + upload.iconClass"
            ></i>
            {{ upload.getName() }}
          </a>
        </li>
      </ul>
    </template>
    <template #content>
      <component
        :is="userFileUploadComponent"
        @uploaded="$emit('uploaded', $event)"
      ></component>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'UserFilesModal',
  mixins: [modal],
  data() {
    return {
      page: null,
    }
  },
  computed: {
    registeredUserFileUploads() {
      return this.$registry.getAll('userFileUpload')
    },
    userFileUploadComponent() {
      const active = Object.values(
        this.$registry.getAll('userFileUpload')
      ).find((upload) => upload.type === this.page)
      return active ? active.getComponent() : null
    },
  },
  methods: {
    setPage(page) {
      this.page = page
    },
    isPage(page) {
      return this.page === page
    },
    show(page, ...args) {
      this.page = page
      return modal.methods.show.call(this, ...args)
    },
  },
}
</script>

<i18n>
{
  "en": {
    "userFilesModal": {
      "title": "Upload from"
    }
  },
  "fr": {
    "userFilesModal": {
      "title": "En provenance"
    }
  }
}
</i18n>
