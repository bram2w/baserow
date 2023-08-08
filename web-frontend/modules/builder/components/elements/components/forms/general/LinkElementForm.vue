<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormulaInputGroup
      v-model="values.value"
      :label="$t('linkElementForm.text')"
      :placeholder="$t('linkElementForm.textPlaceholder')"
      :error="
        !$v.values.value.validFormula ? $t('elementForms.invalidFormula') : ''
      "
    />
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.navigateTo') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="navigateTo" :show-search="false">
          <template #value>
            <template v-if="destinationPage">
              {{ destinationPage.name }}
              <span class="link-element-form__navigate-option-page-path">
                {{ destinationPage.path }}
              </span></template
            >
            <span v-else>{{ $t('linkElementForm.navigateToCustom') }}</span>
          </template>
          <DropdownItem
            v-for="pageItem in pages"
            :key="pageItem.id"
            :value="pageItem.id"
            :name="pageItem.name"
          >
            {{ pageItem.name }}
            <span class="link-element-form__navigate-option-page-path">
              {{ pageItem.path }}
            </span>
          </DropdownItem>
          <DropdownItem
            :name="$t('linkElementForm.navigateToCustom')"
            value="custom"
          ></DropdownItem>
        </Dropdown>
      </div>
    </FormElement>
    <FormElement v-if="navigateTo === 'custom'" class="control">
      <FormulaInputGroup
        v-model="values.navigate_to_url"
        :page="page"
        :label="$t('linkElementForm.url')"
        :placeholder="$t('linkElementForm.urlPlaceholder')"
        :error="
          !$v.values.navigate_to_url.validFormula
            ? $t('elementForms.invalidFormula')
            : ''
        "
        @blur="$v.values.navigate_to_url.$touch()"
      />
    </FormElement>
    <FormElement v-if="destinationPage" class="control">
      <template v-if="parametersInError">
        <Alert type="error" minimal>
          <div class="link-element-form__params-error">
            <div>
              {{ $t('linkElementForm.paramsInErrorDescription') }}
            </div>
            <Button
              type="error"
              size="tiny"
              @click.prevent="updatePageParameters"
            >
              {{ $t('linkElementForm.paramsInErrorButton') }}
            </Button>
          </div>
        </Alert>
      </template>
      <div v-else>
        <div
          v-for="(param, index) in values.page_parameters"
          :key="param.name"
          class="link-element-form__param"
        >
          <FormulaInputGroup
            v-model="param.value"
            :page="page"
            :label="param.name"
            horizontal
            :placeholder="$t('linkElementForm.paramPlaceholder')"
            :error="
              $v.values.page_parameters.$each[index].$dirty &&
              $v.values.page_parameters.$each[index].$error
                ? $t('elementForms.invalidFormula')
                : ''
            "
            @blur="$v.values.page_parameters.$each[index].$touch()"
          />
        </div>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.variant') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.variant" value="link">
          {{ $t('linkElementForm.variantLink') }}
        </RadioButton>
        <RadioButton v-model="values.variant" value="button">
          {{ $t('linkElementForm.variantButton') }}
        </RadioButton>
      </div>
    </FormElement>
    <FormElement class="control">
      <HorizontalAlignmentSelector v-model="values.alignment" />
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.target') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.target" value="self">
          {{ $t('linkElementForm.targetSelf') }}
        </RadioButton>
        <RadioButton v-model="values.target" value="blank">
          {{ $t('linkElementForm.targetNewTab') }}
        </RadioButton>
      </div>
    </FormElement>
    <FormElement v-if="values.variant === 'button'" class="control">
      <label class="control__label">
        {{ $t('linkElementForm.width') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.width" value="auto">
          {{ $t('linkElementForm.widthAuto') }}
        </RadioButton>
        <RadioButton v-model="values.width" value="full">
          {{ $t('linkElementForm.widthFull') }}
        </RadioButton>
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { LinkElementType } from '@baserow/modules/builder/elementTypes'
import HorizontalAlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import { HORIZONTAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import { isValidFormula } from '@baserow/formula'

export default {
  name: 'LinkElementForm',
  components: { HorizontalAlignmentSelector, FormulaInputGroup },
  mixins: [form],
  props: {
    builder: { type: Object, required: true },
    page: { type: Object, required: true },
  },
  data() {
    let navigateTo = ''
    if (this.defaultValues.navigation_type === 'page') {
      if (this.defaultValues.navigate_to_page_id) {
        navigateTo = this.defaultValues.navigate_to_page_id
      }
    } else {
      navigateTo = 'custom'
    }
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
        variant: 'link',
        navigation_type: 'page',
        navigate_to_page_id: null,
        navigate_to_url: '',
        page_parameters: [],
        width: 'auto',
        target: 'self',
      },
      parametersInError: false,
      navigateTo,
    }
  },
  computed: {
    pages() {
      return this.builder.pages
    },
    destinationPage() {
      if (!isNaN(this.navigateTo)) {
        return this.builder.pages.find(({ id }) => id === this.navigateTo)
      }
      return null
    },
  },
  watch: {
    'destinationPage.path_params': {
      handler(value) {
        this.updatePageParameters()
      },
      deep: true,
      immediate: true,
    },
    navigateTo(value) {
      if (value === '') {
        this.values.navigation_type = 'page'
        this.values.navigate_to_page_id = null
        this.values.navigate_to_url = ''
      } else if (value === 'custom') {
        this.values.navigation_type = 'custom'
      } else if (!isNaN(value)) {
        this.values.navigation_type = 'page'
        this.values.navigate_to_page_id = value
        this.updatePageParameters()
      }
    },
    destinationPage(value) {
      this.updatePageParameters()

      // This means that the page select does not exist anymore
      if (value === undefined) {
        this.values.navigate_to_page_id = null
      }
    },
  },
  mounted() {
    if (LinkElementType.arePathParametersInError(this.values, this.builder)) {
      this.parametersInError = true
    }
  },
  methods: {
    getPageParameterType(parameterName) {
      return (this.destinationPage?.path_params || []).find(
        (pathParam) => pathParam.name === parameterName
      )?.type
    },
    updatePageParameters() {
      this.values.page_parameters = (
        this.destinationPage?.path_params || []
      ).map(({ name }, index) => {
        const previousValue = this.values.page_parameters[index]?.value || ''
        return { name, value: previousValue }
      })
      this.parametersInError = false
      this.$v.values.page_parameters.$touch()
    },
    validatePageParameter(pageParameter) {
      return isValidFormula(pageParameter.value)
    },
  },
  validations() {
    return {
      values: {
        value: { validFormula: isValidFormula },
        page_parameters: {
          $each: { $validator: this.validatePageParameter },
        },
        navigate_to_url: { validFormula: isValidFormula },
      },
    }
  },
}
</script>
