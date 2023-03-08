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
              @click.stop="$refs.rename.edit()"
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
          @click.stop="previous()"
        >
          <i class="fas fa-chevron-left"></i>
        </a>
        <a
          class="file-field-modal__body-nav file-field-modal__body-nav--next"
          @click.stop="next()"
        >
          <i class="fas fa-chevron-right"></i>
        </a>
        <div v-if="preview !== null" class="file-field-modal__preview">
          <PreviewAny
            ref="modalPreview"
            :mime-type="preview.mime_type"
            :url="preview.url"
          >
            <template #fallback>
              <div class="file-field-modal__preview-icon">
                <i class="fas" :class="getIconClass(preview.mime_type)"></i>
              </div>
            </template>
          </PreviewAny>
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
              @click.stop="selected = index"
            >
              <img
                v-if="file.is_image"
                :src="file.thumbnails.small.url"
                class="file-field-modal__nav-image"
              />
              <i
                v-else
                class="fas file-field-modal__nav-icon"
                :class="getIconClass(file.mime_type)"
              ></i>
            </a>
          </li>
        </ul>
        <ul v-if="preview" class="file-field-modal__actions">
          <DownloadLink
            class="file-field-modal__action"
            :url="preview.url"
            :filename="preview.visible_name"
            :loading-class="'file-field-modal__action--loading'"
            ><i class="fas fa-download" @click.stop=""></i
          ></DownloadLink>
          <a
            v-if="!readOnly"
            class="file-field-modal__action"
            @click.stop="remove(selected)"
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
import PreviewAny from '@baserow/modules/database/components/preview/PreviewAny'

export default {
  name: 'FileFieldModal',
  components: {
    PreviewAny,
  },
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
      canClose: true,
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
      return 'fa-' + mimetype2fa(mimeType)
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
      if (event.key === 'ArrowLeft') {
        this.previous()
      }
      // If right arrow
      if (event.key === 'ArrowRight') {
        this.next()
      }
      return baseModal.methods.keyup.call(this, event)
    },
    outside(event) {
      if (event.target === this.$refs.rename.$el) {
        return
      }
      const modalPreview = this.$refs.modalPreview.$el
      const targetClassname = event.target.className
      const isPreviewImage =
        !!modalPreview.getElementsByClassName(targetClassname).length
      if (!isPreviewImage && this.canClose) {
        this.hide()
      }
    },
  },
}
</script>
