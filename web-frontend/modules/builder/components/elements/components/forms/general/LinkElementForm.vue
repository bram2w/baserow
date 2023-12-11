<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('linkElementForm.text')"
      :placeholder="$t('linkElementForm.textPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
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
      <ApplicationBuilderFormulaInputGroup
        v-model="values.navigate_to_url"
        :page="page"
        :label="$t('linkElementForm.url')"
        :placeholder="$t('linkElementForm.urlPlaceholder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      />
    </FormElement>
    <FormElement v-if="destinationPage" class="control">
      <template v-if="parametersInError">
        <Alert type="error">
          <p>
            {{ $t('linkElementForm.paramsInErrorDescription') }}
          </p>
          <template #actions>
            <button
              class="alert__actions-button-text"
              @click.prevent="updatePageParameters"
            >
              {{ $t('linkElementForm.paramsInErrorButton') }}
            </button>
          </template>
        </Alert>
      </template>
      <div v-else>
        <div
          v-for="param in values.page_parameters"
          :key="param.name"
          class="link-element-form__param"
        >
          <ApplicationBuilderFormulaInputGroup
            v-model="param.value"
            :page="page"
            :label="param.name"
            horizontal
            :placeholder="$t('linkElementForm.paramPlaceholder')"
            :data-providers-allowed="DATA_PROVIDERS_ALLOWED_PAGE_PARAMETERS"
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
      <WidthSelector v-model="values.width" />
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { LinkElementType } from '@baserow/modules/builder/elementTypes'
import HorizontalAlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import {
  DATA_PROVIDERS_ALLOWED_ELEMENTS,
  HORIZONTAL_ALIGNMENTS,
  WIDTHS,
} from '@baserow/modules/builder/enums'
import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'
import { PageParameterDataProviderType } from '@baserow/modules/builder/dataProviderTypes'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'LinkElementForm',
  components: {
    WidthSelector,
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentSelector,
  },
  mixins: [form],
  inject: ['builder', 'page'],
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
        width: WIDTHS.AUTO.value,
        target: 'self',
      },
      parametersInError: false,
      navigateTo,
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
    DATA_PROVIDERS_ALLOWED_PAGE_PARAMETERS() {
      const PROVIDERS_TO_REMOVE = [
        new PageParameterDataProviderType().getType(),
      ]
      return this.DATA_PROVIDERS_ALLOWED_ELEMENTS.filter(
        (dataProvider) => !PROVIDERS_TO_REMOVE.includes(dataProvider)
      )
    },
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
    updatePageParameters() {
      this.values.page_parameters = (
        this.destinationPage?.path_params || []
      ).map(({ name }, index) => {
        const previousValue = this.values.page_parameters[index]?.value || ''
        return { name, value: previousValue }
      })
      this.parametersInError = false
    },
  },
}
</script>
