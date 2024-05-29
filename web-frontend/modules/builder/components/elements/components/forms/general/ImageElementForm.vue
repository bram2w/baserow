<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('imageElementForm.fileLabel') }}
      </label>
      <div class="control__elements">
        <RadioGroup
          v-model="values.image_source_type"
          :options="imageSourceTypeOptions"
          type="button"
        >
        </RadioGroup>
      </div>
    </FormElement>
    <FormElement
      v-if="values.image_source_type === IMAGE_SOURCE_TYPES.UPLOAD"
      class="control"
    >
      <Button
        v-if="values.image_file === null"
        type="upload"
        @click="openFileUploadModal"
      >
        {{ $t('imageElementForm.uploadFileButton') }}
      </Button>

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
    <FormElement class="control">
      <FormInput
        v-model="values.style_max_width"
        :label="$t('imageElementForm.maxWidthLabel')"
        type="number"
        icon-right="iconoir-percentage"
        :placeholder="$t('imageElementForm.maxWidthPlaceholder')"
        :to-value="(value) => (value ? parseInt(value) : null)"
        :error="
          $v.values.style_max_width.$dirty && !$v.values.style_max_width.integer
            ? $t('error.integerField')
            : !$v.values.style_max_width.minValue
            ? $t('error.minValueField', { min: 0 })
            : !$v.values.style_max_width.maxValue
            ? $t('error.maxValueField', { max: 100 })
            : ''
        "
      ></FormInput>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">{{
        $t('imageElementForm.maxHeightLabel')
      }}</label>
      <div class="control__elements">
        <FormInput
          v-model="styleMaxHeight"
          type="number"
          icon-right="iconoir-ruler-combine"
          class="margin-top-1"
          :placeholder="$t('imageElementForm.maxHeightPlaceholder')"
          :to-value="(value) => (value ? parseInt(value) : null)"
          :error="
            $v.values.style_max_height.$dirty &&
            !$v.values.style_max_height.integer
              ? $t('error.integerField')
              : !$v.values.style_max_height.minValue
              ? $t('error.minValueField', { min: 5 })
              : !$v.values.style_max_height.maxValue
              ? $t('error.maxValueField', { max: 3000 })
              : ''
          "
        ></FormInput>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">{{
        $t('imageElementForm.imageConstraintsLabel')
      }}</label>
      <Dropdown v-model="values.style_image_constraint" :show-search="true">
        <DropdownItem
          v-for="{ name, label } in imageConstraintChoices"
          :key="name"
          :disabled="constraintDisabled(name)"
          :description="
            constraintDisabled(name)
              ? $t(`imageElementForm.imageConstraint${label}Disabled`)
              : ''
          "
          :name="label"
          :value="name"
        >
        </DropdownItem>
      </Dropdown>
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
import { integer, maxValue, minValue } from 'vuelidate/lib/validators'

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
        style_max_width: 100,
        style_max_height: null,
        style_image_constraint: 'contain',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
      },
    }
  },
  computed: {
    styleMaxHeight: {
      get() {
        return this.values.style_max_height
      },
      set(newValue) {
        // If the `style_max_height` is emptied, and the
        // constraint is 'cover', then reset back to 'contain'.
        if (!newValue && this.values.style_image_constraint === 'cover') {
          this.values.style_image_constraint = 'contain'
        }
        // If the `style_max_height` is set, and the
        // constraint is 'contain', then reset back to 'cover'.
        if (newValue && this.values.style_image_constraint === 'contain') {
          this.values.style_image_constraint = 'cover'
        }
        this.values.style_max_height = newValue
      },
    },
    IMAGE_SOURCE_TYPES() {
      return IMAGE_SOURCE_TYPES
    },
    imageSourceTypeOptions() {
      return [
        {
          label: this.$t('imageElementForm.fileSourceTypeUpload'),
          value: IMAGE_SOURCE_TYPES.UPLOAD,
        },
        {
          label: this.$t('imageElementForm.fileSourceTypeURL'),
          value: IMAGE_SOURCE_TYPES.URL,
        },
      ]
    },
    IMAGE_FILE_TYPES() {
      return IMAGE_FILE_TYPES
    },
    imageConstraintChoices() {
      return [
        {
          name: 'full-width',
          label: this.$t('imageElementForm.imageConstraintFullWidth'),
        },
        {
          name: 'contain',
          label: this.$t('imageElementForm.imageConstraintContain'),
        },
        {
          name: 'cover',
          label: this.$t('imageElementForm.imageConstraintCover'),
        },
      ]
    },
  },
  methods: {
    constraintDisabled(name) {
      if (name === 'cover') {
        return !this.values.style_max_height
      } else if (name === 'contain') {
        return !!(
          this.values.style_max_height && this.values.style_max_height > 0
        )
      }
    },
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
      style_max_width: {
        integer,
        minValue: minValue(0),
        maxValue: maxValue(100),
      },
      style_max_height: {
        integer,
        minValue: minValue(5),
        maxValue: maxValue(3000),
      },
    },
  },
}
</script>
