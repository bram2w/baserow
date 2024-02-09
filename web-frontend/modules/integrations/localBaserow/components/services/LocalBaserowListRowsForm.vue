<template>
  <form @submit.prevent>
    <div class="row">
      <div class="col col-12">
        <LocalBaserowTableSelector
          v-model="fakeTableId"
          :databases="databases"
          :view-id.sync="values.view_id"
        ></LocalBaserowTableSelector>
      </div>
    </div>
    <div class="row">
      <div class="col col-12">
        <Tabs>
          <Tab
            :title="$t('localBaserowListRowsForm.filterTabTitle')"
            class="data-source-form__condition-form-tab"
          >
            <LocalBaserowTableServiceConditionalForm
              v-if="values.table_id && dataSource.schema"
              v-model="values.filters"
              :schema="dataSource.schema"
              :table-loading="tableLoading"
              :filter-type.sync="values.filter_type"
            >
            </LocalBaserowTableServiceConditionalForm>
            <p v-if="!values.table_id">
              {{ $t('localBaserowListRowsForm.noTableChosenForFiltering') }}
            </p>
          </Tab>
          <Tab
            :title="$t('localBaserowListRowsForm.sortTabTitle')"
            class="data-source-form__sort-form-tab"
          >
            <LocalBaserowTableServiceSortForm
              v-if="values.table_id && dataSource.schema"
              v-model="values.sortings"
              :schema="dataSource.schema"
              :table-loading="tableLoading"
            ></LocalBaserowTableServiceSortForm>
            <p v-if="!values.table_id">
              {{ $t('localBaserowListRowsForm.noTableChosenForSorting') }}
            </p>
          </Tab>
          <Tab
            :title="$t('localBaserowListRowsForm.searchTabTitle')"
            class="data-source-form__search-form-tab"
          >
            <InjectedFormulaInputGroup
              v-model="values.search_query"
              :placeholder="
                $t('localBaserowListRowsForm.searchFieldPlaceHolder')
              "
            />
          </Tab>
        </Tabs>
      </div>
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import LocalBaserowTableSelector from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableSelector'
import LocalBaserowTableServiceConditionalForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableServiceConditionalForm'
import LocalBaserowTableServiceSortForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableServiceSortForm'
import { DATA_PROVIDERS_ALLOWED_DATA_SOURCES } from '@baserow/modules/builder/enums'
import InjectedFormulaInputGroup from '@baserow/modules/core/components/formula/InjectedFormulaInputGroup'

export default {
  components: {
    InjectedFormulaInputGroup,
    LocalBaserowTableSelector,
    LocalBaserowTableServiceSortForm,
    LocalBaserowTableServiceConditionalForm,
  },
  mixins: [form],
  inject: ['page'],
  provide() {
    return { dataProvidersAllowed: DATA_PROVIDERS_ALLOWED_DATA_SOURCES }
  },
  props: {
    builder: {
      type: Object,
      required: true,
    },
    contextData: { type: Object, required: true },
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
        'search_query',
        'filters',
        'filter_type',
        'sortings',
      ],
      values: {
        table_id: null,
        view_id: null,
        search_query: '',
        filters: [],
        sortings: [],
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
        // and `sortings` to a blank array, and `view_id` to `null`.
        if (this.values.table_id && this.values.table_id !== newValue) {
          this.values.filters = []
          this.values.sortings = []
          this.values.view_id = null
        }
        this.values.table_id = newValue
      },
    },
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
