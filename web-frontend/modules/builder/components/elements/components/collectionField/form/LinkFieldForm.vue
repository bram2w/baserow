<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.link_name"
      :label="$t('linkFieldForm.fieldLinkNameLabel')"
      :placeholder="$t('linkFieldForm.fieldLinkNamePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :application-context-additions="{
        element,
      }"
      horizontal
    />
    <FormGroup :label="$t('linkNavigationSelection.navigateTo')" small-label>
      <Dropdown v-model="navigateTo" :show-search="false">
        <template #value>
          <template v-if="destinationPage">
            {{ destinationPage.name }}
            <span class="link-field-form__navigate-option-page-path">
              {{ destinationPage.path }}
            </span></template
          >
          <span v-else>{{
            $t('linkNavigationSelection.navigateToCustom')
          }}</span>
        </template>
        <DropdownItem
          v-for="pageItem in pages"
          :key="pageItem.id"
          :value="pageItem.id"
          :name="pageItem.name"
        >
          {{ pageItem.name }}
          <span class="link-field-form__navigate-option-page-path">
            {{ pageItem.path }}
          </span>
        </DropdownItem>
        <DropdownItem
          :name="$t('linkNavigationSelection.navigateToCustom')"
          value="custom"
        ></DropdownItem>
      </Dropdown>
    </FormGroup>

    <FormGroup v-if="navigateTo === 'custom'">
      <ApplicationBuilderFormulaInputGroup
        v-model="values.navigate_to_url"
        :page="page"
        :label="$t('linkNavigationSelection.url')"
        :placeholder="$t('linkNavigationSelection.urlPlaceholder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
        :application-context-additions="{
          element,
        }"
      />
    </FormGroup>

    <FormGroup v-if="destinationPage">
      <template v-if="parametersInError">
        <Alert type="error">
          <p>
            {{ $t('linkNavigationSelection.paramsInErrorDescription') }}
          </p>
          <template #actions>
            <button
              class="alert__actions-button-text"
              @click.prevent="updatePageParameters"
            >
              {{ $t('linkNavigationSelection.paramsInErrorButton') }}
            </button>
          </template>
        </Alert>
      </template>
      <div v-else>
        <div
          v-for="param in values.page_parameters"
          :key="param.name"
          class="link-field-form__param"
        >
          <ApplicationBuilderFormulaInputGroup
            v-model="param.value"
            :page="page"
            :label="param.name"
            horizontal
            :placeholder="$t('linkNavigationSelection.paramPlaceholder')"
            :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
            :application-context-additions="{
              element,
            }"
          />
        </div>
      </div>
    </FormGroup>
  </form>
</template>

<script>
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import { pathParametersInError } from '@baserow/modules/builder/utils/params'

export default {
  name: 'TextField',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  inject: ['page', 'builder'],
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
  data() {
    let navigateTo = ''
    if (this.defaultValues.navigation_type === 'page') {
      if (this.defaultValues.navigate_to_page_id) {
        navigateTo = this.defaultValues.navigate_to_page_id
      }
    } else if (this.defaultValues.navigation_type === 'custom') {
      navigateTo = 'custom'
    }
    return {
      allowedValues: [
        'link_name',
        'navigate_to_url',
        'navigation_type',
        'navigate_to_page_id',
        'page_parameters',
      ],
      values: {
        link_name: '',
        navigate_to_url: '',
        navigation_type: 'page',
        navigate_to_page_id: null,
        page_parameters: [],
      },
      parametersInError: false,
      navigateTo,
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS() {
      return DATA_PROVIDERS_ALLOWED_ELEMENTS
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
        this.refreshParametersInError()
      },
      deep: true,
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
    this.refreshParametersInError()
  },
  methods: {
    refreshParametersInError() {
      this.parametersInError = pathParametersInError(this.values, this.builder)
    },
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
