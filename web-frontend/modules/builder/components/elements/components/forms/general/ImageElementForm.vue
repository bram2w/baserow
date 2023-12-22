<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('imageElementForm.fileLabel') }}
      </label>
      <div class="control__elements">
        <RadioButton
          v-model="values.image_source_type"
          :value="IMAGE_SOURCE_TYPES.UPLOAD"
        >
          {{ $t('imageElementForm.fileSourceTypeUpload') }}
        </RadioButton>
        <RadioButton
          v-model="values.image_source_type"
          :value="IMAGE_SOURCE_TYPES.URL"
        >
          {{ $t('imageElementForm.fileSourceTypeURL') }}
        </RadioButton>
      </div>
    </FormElement>
    <FormElement
      v-if="values.image_source_type === IMAGE_SOURCE_TYPES.UPLOAD"
      class="control"
    >
      <button
        v-if="values.image_file === null"
        class="button"
        @click="openFileUploadModal"
      >
        {{ $t('imageElementForm.uploadFileButton') }}
      </button>
      <Thumbnail
        v-else
        removable
        :src="values.image_file.url"
        @remove="values.image_file = null"
      />
      <UserFilesModal
        ref="userFilesModal"
        :multiple-files="false"
        :file-types-acceptable="IMAGE_FILE_TYPES"
        @uploaded="fileUploaded"
      />
    </FormElement>
    <FormElement
      v-if="values.image_source_type === IMAGE_SOURCE_TYPES.URL"
      class="control"
    >
      <div class="control__elements">
        <div class="control__description">
          {{ $t('imageElementForm.urlWarning') }}
        </div>
        <ApplicationBuilderFormulaInputGroup
          v-model="values.image_url"
          :placeholder="$t('elementForms.urlInputPlaceholder')"
          :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
        />
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('imageElementForm.altTextTitle') }}
      </label>
      <div class="control__description">
        {{ $t('imageElementForm.altTextDescription') }}
      </div>
      <div class="control__elements">
        <ApplicationBuilderFormulaInputGroup
          v-model="values.alt_text"
          :placeholder="$t('elementForms.textInputPlaceholder')"
          :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
        />
      </div>
    </FormElement>
    <FormElement class="control">
      <HorizontalAlignmentSelector v-model="values.alignment" />
    </FormElement>
  </form>
</template>

<script>
import {
  HORIZONTAL_ALIGNMENTS,
  IMAGE_SOURCE_TYPES,
} from '@baserow/modules/builder/enums'
import { IMAGE_FILE_TYPES } from '@baserow/modules/core/enums'
import UserFilesModal from '@baserow/modules/core/components/files/UserFilesModal'
import { UploadFileUserFileUploadType } from '@baserow/modules/core/userFileUploadTypes'
import HorizontalAlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'ImageElementForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentSelector,
    UserFilesModal,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        image_source_type: IMAGE_SOURCE_TYPES.UPLOAD,
        image_file: null,
        image_url: '',
        alt_text: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
      },
    }
  },
  computed: {
    IMAGE_SOURCE_TYPES() {
      return IMAGE_SOURCE_TYPES
    },
    IMAGE_FILE_TYPES() {
      return IMAGE_FILE_TYPES
    },
  },
  methods: {
    openFileUploadModal() {
      this.$refs.userFilesModal.show(UploadFileUserFileUploadType.getType())
    },
    fileUploaded([file]) {
      this.values.image_file = file
      this.$refs.userFilesModal.hide()
    },
  },
}
</script>
