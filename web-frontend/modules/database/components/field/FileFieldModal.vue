<template>
  <div
    v-if="open"
    ref="modalWrapper"
    class="modal__wrapper file-field-modal__wrapper"
    @click="outside($event)"
  >
    <div class="file-field-modal">
      <div class="file-field-modal__head">
        <div class="file-field-modal__name">
          <template v-if="preview">
            <Editable
              ref="rename"
              :value="preview.visible_name"
              @change="
                $emit('renamed', {
                  value: files,
                  index: selected,
                  value: $event.value,
                })
              "
              @editing="renaming = $event"
            ></Editable>
            <a
              v-if="!readOnly"
              v-show="!renaming"
              class="file-field-modal__rename"
              @click="$refs.rename.edit()"
            >
              <i class="fa fa-pen"></i>
            </a>
          </template>
        </div>
        <a class="file-field-modal__close" @click="hide()">
          <i class="fas fa-times"></i>
        </a>
      </div>
      <div class="file-field-modal__body">
        <a
          class="
            file-field-modal__body-nav file-field-modal__body-nav--previous
          "
          @click="previous()"
        >
          <i class="fas fa-chevron-left"></i>
        </a>
        <a
          class="file-field-modal__body-nav file-field-modal__body-nav--next"
          @click="next()"
        >
          <i class="fas fa-chevron-right"></i>
        </a>
        <div v-if="preview !== null" class="file-field-modal__preview">
          <FileFieldModalImage
            v-if="preview.is_image"
            :key="preview.name + '-' + selected"
            :src="preview.url"
          ></FileFieldModalImage>
          <div v-else class="file-field-modal__preview-icon">
            <i class="fas" :class="'fa-' + getIconClass(preview.mime_type)"></i>
          </div>
        </div>
      </div>
      <div class="file-field-modal__foot">
        <ul class="file-field-modal__nav">
          <li
            v-for="(file, index) in files"
            :key="file.name + '-' + index"
            class="file-field-modal__nav-item"
          >
            <a
              class="file-field-modal__nav-link"
              :class="{ active: index === selected }"
              @click="selected = index"
            >
              <img
                v-if="file.is_image"
                :src="file.thumbnails.small.url"
                class="file-field-modal__nav-image"
              />
              <i
                v-else
                class="fas file-field-modal__nav-icon"
                :class="'fa-' + getIconClass(file.mime_type)"
              ></i>
            </a>
          </li>
        </ul>
        <ul v-if="preview" class="file-field-modal__actions">
          <a
            target="_blank"
            :href="preview.url"
            class="file-field-modal__action"
          >
            <i class="fas fa-download"></i>
          </a>
          <a
            v-if="!readOnly"
            class="file-field-modal__action"
            @click="remove(selected)"
          >
            <i class="fas fa-trash"></i>
          </a>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import baseModal from '@baserow/modules/core/mixins/baseModal'
import { mimetype2fa } from '@baserow/modules/core/utils/fontawesome'
import FileFieldModalImage from '@baserow/modules/database/components/field/FileFieldModalImage'

export default {
  name: 'FileFieldModal',
  components: { FileFieldModalImage },
  mixins: [baseModal],
  props: {
    files: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      renaming: false,
      selected: 0,
    }
  },
  computed: {
    preview() {
      if (this.files.length > this.selected) {
        return this.files[this.selected]
      }
      return null
    },
  },
  methods: {
    show(index = 0) {
      this.selected = index
      return baseModal.methods.show.call(this)
    },
    getIconClass(mimeType) {
      return mimetype2fa(mimeType)
    },
    next() {
      this.selected =
        this.files.length - 1 > this.selected ? this.selected + 1 : 0
    },
    previous() {
      this.selected =
        this.selected === 0 ? this.files.length - 1 : this.selected - 1
    },
    remove(index) {
      if (index === this.files.length - 1) {
        this.selected = 0
      }

      const length = this.files.length
      this.$emit('removed', index)

      if (length === 1) {
        this.hide()
      }
    },
    keyup(event) {
      // When we are renaming we want the arrow keys to be available to move the
      // cursor.
      if (this.renaming) {
        return
      }

      // If left arrow
      if (event.keyCode === 37) {
        this.previous()
      }
      // If right arrow
      if (event.keyCode === 39) {
        this.next()
      }
      return baseModal.methods.keyup.call(this, event)
    },
  },
}
</script>
