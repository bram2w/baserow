<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup
      :label="$t('linkNavigationSelection.navigateTo')"
      small-label
      class="margin-bottom-2"
      required
    >
      <Dropdown v-model="navigateTo" :show-search="false" small>
        <template #value>
          <template v-if="destinationPage">
            {{ destinationPage.name }}
            <span
              class="link-navigation-selection-form__navigate-option-page-path"
            >
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
          <span
            class="link-navigation-selection-form__navigate-option-page-path"
          >
            {{ pageItem.path }}
          </span>
        </DropdownItem>
        <DropdownItem
          :name="$t('linkNavigationSelection.navigateToCustom')"
          value="custom"
        ></DropdownItem>
      </Dropdown>
    </FormGroup>
    <FormGroup v-if="navigateTo === 'custom'" class="margin-bottom-2" required>
      <ApplicationBuilderFormulaInputGroup
        v-model="values.navigate_to_url"
        :page="page"
        :label="$t('linkNavigationSelection.url')"
        :placeholder="$t('linkNavigationSelection.urlPlaceholder')"
        :data-providers-allowed="dataProvidersAllowed"
        small
      />
    </FormGroup>
    <FormGroup v-if="destinationPage" class="margin-bottom-2" required>
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
        <div v-for="param in values.page_parameters" :key="param.name" required>
          <ApplicationBuilderFormulaInputGroup
            v-model="param.value"
            :page="page"
            :label="param.name"
            horizontal
            :placeholder="$t('linkNavigationSelection.paramPlaceholder')"
            :data-providers-allowed="dataProvidersAllowed"
            small
          />
        </div>
      </div>
    </FormGroup>
    <FormGroup
      small-label
      :label="$t('linkNavigationSelection.target')"
      class="margin-bottom-2"
      required
    >
      <RadioGroup
        v-model="values.target"
        type="button"
        :options="linkNavigationSelectionTargetOptions"
      ></RadioGroup>
    </FormGroup>
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { pathParametersInError } from '@baserow/modules/builder/utils/params'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'LinkNavigationSelectionForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
  },
  mixins: [elementForm],
  props: {
    dataProvidersAllowed: {
      type: Array,
      required: false,
      default: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
    },
  },
  data() {
    return {
      parametersInError: false,
      navigateTo: '',
      allowedValues: [
        'navigation_type',
        'navigate_to_page_id',
        'navigate_to_url',
        'page_parameters',
        'target',
      ],
      values: {
        navigation_type: 'page',
        navigate_to_page_id: null,
        navigate_to_url: '',
        page_parameters: [],
        target: 'self',
      },
      linkNavigationSelectionTargetOptions: [
        { value: 'self', label: this.$t('linkNavigationSelection.targetSelf') },
        {
          value: 'blank',
          label: this.$t('linkNavigationSelection.targetNewTab'),
        },
      ],
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
    if (typeof this.defaultValues.navigation_type !== 'undefined') {
      let navigateTo = ''
      if (this.defaultValues.navigation_type === 'page') {
        if (this.defaultValues.navigate_to_page_id) {
          navigateTo = this.defaultValues.navigate_to_page_id
        }
      } else {
        navigateTo = 'custom'
      }
      this.navigateTo = navigateTo
    }
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
