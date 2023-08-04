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
      :error="fieldHasErrors('image_url')"
    >
      <div class="control__elements">
        <div class="control__description">
          {{ $t('imageElementForm.urlWarning') }}
        </div>
        <input
          v-model="values.image_url"
          :class="{ 'input--error': fieldHasErrors('image_url') }"
          class="input"
          type="url"
          :placeholder="$t('elementForms.urlInputPlaceholder')"
          @blur="$v.values.image_url.$touch()"
        />
        <div
          v-if="
            fieldHasErrors('image_url') &&
            !$v.values.image_url.isValidAbsoluteURL
          "
          class="error"
        >
          {{ $t('imageElementForm.invalidUrlError') }}
        </div>
        <div
          v-if="fieldHasErrors('image_url') && !$v.values.image_url.maxLength"
          class="error"
        >
          {{ $t('error.maxLength', { max: 1000 }) }}
        </div>
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
        <input
          v-model="values.alt_text"
          :placeholder="$t('elementForms.textInputPlaceholder')"
          type="text"
          class="input"
        />
      </div>
    </FormElement>
    <FormElement class="control">
      <AlignmentSelector v-model="values.alignment" />
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { isValidAbsoluteURL } from '@baserow/modules/core/utils/string'
import { ALIGNMENTS, IMAGE_SOURCE_TYPES } from '@baserow/modules/builder/enums'
import { IMAGE_FILE_TYPES } from '@baserow/modules/core/enums'
import UserFilesModal from '@baserow/modules/core/components/files/UserFilesModal'
import { UploadFileUserFileUploadType } from '@baserow/modules/core/userFileUploadTypes'
import AlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/settings/AlignmentSelector'
import { maxLength } from 'vuelidate/lib/validators'

export default {
  name: 'ImageElementForm',
  components: { AlignmentSelector, UserFilesModal },
  mixins: [form],
  data() {
    return {
      values: {
        image_source_type: IMAGE_SOURCE_TYPES.UPLOAD,
        image_file: null,
        image_url: '',
        alt_text: '',
        alignment: ALIGNMENTS.LEFT.value,
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
  validations: {
    values: {
      image_url: {
        isValidAbsoluteURL: (value) =>
          isValidAbsoluteURL(value) || value === '',
        maxLength: maxLength(1000),
      },
    },
  },
}
</script>
