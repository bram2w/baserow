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
              v-if="values.table_id"
              v-model="dataSourceFilters"
              :fields="tableFields"
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
              v-if="values.table_id"
              v-model="dataSourceSortings"
              :fields="tableFields"
            ></LocalBaserowTableServiceSortForm>
            <p v-if="!values.table_id">
              {{ $t('localBaserowListRowsForm.noTableChosenForSorting') }}
            </p>
          </Tab>
          <Tab
            :title="$t('localBaserowListRowsForm.searchTabTitle')"
            class="data-source-form__search-form-tab"
          >
            <InjectedFormulaInput
              v-model="values.search_query"
              small
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
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'

export default {
  components: {
    InjectedFormulaInput,
    LocalBaserowTableSelector,
    LocalBaserowTableServiceSortForm,
    LocalBaserowTableServiceConditionalForm,
  },
  mixins: [form],
  inject: ['page'],
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
    dataSourceFilters: {
      get() {
        return this.excludeTrashedFields(this.values.filters)
      },
      set(newValue) {
        this.values.filters = newValue
      },
    },
    dataSourceSortings: {
      get() {
        return this.excludeTrashedFields(this.values.sortings)
      },
      set(newValue) {
        this.values.sortings = newValue
      },
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
    tables() {
      return this.databases.map((database) => database.tables).flat()
    },
    tableSelected() {
      return this.tables.find(({ id }) => id === this.values.table_id)
    },
    tableFields() {
      return this.tableSelected?.fields || []
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
  methods: {
    /**
     * Given an array of objects containing a `field` property (e.g. the data
     * source filters or sortings arrays), this method will return a new array
     * containing only the objects where the field is part of the schema, so,
     * untrashed.
     *
     * @param {Array} value - The array of objects to filter.
     * @returns {Array} - The filtered array.
     */
    excludeTrashedFields(value) {
      const localBaserowFieldIds = this.tableFields.map(({ id }) => id)
      return value.filter(({ field }) => localBaserowFieldIds.includes(field))
    },
  },
}
</script>
