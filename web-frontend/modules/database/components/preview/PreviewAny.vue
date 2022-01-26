<template>
  <div :key="url" class="preview">
    <component
      :is="compatibleTypes[selectedPreview || 0].getPreviewComponent()"
      v-if="
        (compatibleTypes.length === 1 && externalTypes.length === 0) ||
        selectedPreview !== null
      "
      :url="url"
      :mime-type="mimeType"
    >
      <template #fallback><slot name="fallback" /></template>
    </component>
    <div
      v-else-if="compatibleTypes.length > 1 || externalTypes.length === 1"
      class="preview__select"
    >
      <slot name="fallback" />
      <div v-if="externalTypes" class="preview__select-warning">
        {{ $t('previewAny.externalWarning') }}
      </div>
      <div class="preview__select-buttons">
        <button
          v-for="(preview, index) in compatibleTypes"
          :key="preview.getType()"
          class="button button--ghost"
          @click.prevent.stop="selectedPreview = index"
        >
          <i
            v-if="preview.isExternal()"
            class="button__icon fas fa-lock-open"
          ></i>
          {{ preview.getName() }}
        </button>
      </div>
    </div>
    <slot v-else name="fallback" />
  </div>
</template>

<script>
import PreviewImage from '@baserow/modules/database/components/preview/PreviewImage'
import PreviewAudio from '@baserow/modules/database/components/preview/PreviewAudio'
import PreviewVideo from '@baserow/modules/database/components/preview/PreviewVideo'

export default {
  name: 'PreviewAny',
  components: {
    PreviewImage,
    PreviewAudio,
    PreviewVideo,
  },
  props: {
    mimeType: {
      type: String,
      required: true,
    },
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      selectedPreview: null,
    }
  },
  computed: {
    // Allow to watch url property
    currentUrl() {
      return this.url
    },
    previewTypes() {
      return Object.entries(this.$registry.getAll('preview')).map(
        ([, type]) => type
      )
    },
    compatibleTypes() {
      return this.previewTypes
        .filter((previewType) =>
          previewType.isCompatible(this.mimeType, this.url)
        )
        .sort(
          (previewTypeA, previewTypeB) =>
            previewTypeA.getOrder() - previewTypeB.getOrder()
        )
    },
    externalTypes() {
      return this.compatibleTypes.filter((type) => type.isExternal())
    },
  },
  watch: {
    // On url change we reset the selectedPreview type
    currentUrl() {
      this.selectedPreview = null
    },
  },
}
</script>
