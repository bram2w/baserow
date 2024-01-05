<template>
  <form @submit.prevent>
    <div>
      <div class="row">
        <div class="col col-12">
          <LocalBaserowTableSelector
            v-model="fakeTableId"
            class="local-baserow-get-row-form__table-selector"
            :databases="databases"
            :view-id.sync="values.view_id"
          ></LocalBaserowTableSelector>
        </div>
      </div>
      <div class="row">
        <div class="col col-6">
          <ApplicationBuilderFormulaInputGroup
            v-model="values.row_id"
            small-label
            :label="$t('localBaserowGetRowForm.rowFieldLabel')"
            :placeholder="$t('localBaserowGetRowForm.rowFieldPlaceHolder')"
            :help-text="$t('localBaserowGetRowForm.rowFieldHelpText')"
            :data-providers-allowed="DATA_PROVIDERS_ALLOWED_DATA_SOURCES"
          />
        </div>
      </div>
      <div class="row">
        <div class="col col-12">
          <Tabs>
            <Tab
              :title="$t('localBaserowGetRowForm.filterTabTitle')"
              class="data-source-form__condition-form-tab"
            >
              <LocalBaserowTableServiceConditionalForm
                v-if="values.table_id && dataSource.schema"
                v-model="values.filters"
                :schema="dataSource.schema"
                :table-loading="tableLoading"
                :filter-type.sync="values.filter_type"
              />
              <p v-if="!values.table_id">
                {{ $t('localBaserowGetRowForm.noTableChosenForFiltering') }}
              </p>
            </Tab>
            <Tab :title="$t('localBaserowGetRowForm.searchTabTitle')">
              <FormInput
                v-model="values.search_query"
                type="text"
                small-label
                :placeholder="
                  $t('localBaserowGetRowForm.searchFieldPlaceHolder')
                "
              />
            </Tab>
          </Tabs>
        </div>
      </div>
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { DATA_PROVIDERS_ALLOWED_DATA_SOURCES } from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import LocalBaserowTableSelector from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableSelector'
import LocalBaserowTableServiceConditionalForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableServiceConditionalForm.vue'

export default {
  components: {
    LocalBaserowTableSelector,
    LocalBaserowTableServiceConditionalForm,
    ApplicationBuilderFormulaInputGroup,
  },
  mixins: [form],
  inject: ['page'],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    contextData: {
      type: Object,
      required: false,
      default: () => ({
        databases: [],
      }),
    },
    dataSource: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: [
        'table_id',
        'view_id',
        'row_id',
        'search_query',
        'filters',
        'filter_type',
      ],
      values: {
        table_id: null,
        view_id: null,
        row_id: '',
        search_query: '',
        filters: [],
        filter_type: 'AND',
      },
      tableLoading: false,
    }
  },
  computed: {
    dataSourceLoading() {
      return this.$store.getters['dataSource/getLoading'](this.page)
    },
    fakeTableId: {
      get() {
        return this.values.table_id
      },
      set(newValue) {
        // If we currently have a `table_id` selected, and the `newValue`
        // is different to the current `table_id`, then reset the `filters`
        // to a blank array, and `view_id` to `null`.
        if (this.values.table_id && this.values.table_id !== newValue) {
          this.values.filters = []
          this.values.view_id = null
        }
        this.values.table_id = newValue
      },
    },
    DATA_PROVIDERS_ALLOWED_DATA_SOURCES: () =>
      DATA_PROVIDERS_ALLOWED_DATA_SOURCES,
    databases() {
      return this.contextData?.databases || []
    },
  },
  watch: {
    'values.table_id'(newValue, oldValue) {
      if (oldValue && newValue !== oldValue) {
        this.tableLoading = true
      }
    },
    dataSourceLoading: {
      handler() {
        this.tableLoading = false
      },
      immediate: true,
    },
  },
}
</script>
