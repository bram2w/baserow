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
          <FormGroup
            small-label
            :label="$t('localBaserowGetRowForm.rowFieldLabel')"
            required
          >
            <InjectedFormulaInput
              v-model="values.row_id"
              :placeholder="$t('localBaserowGetRowForm.rowFieldPlaceHolder')"
            />
            <template #helper>
              {{ $t('localBaserowGetRowForm.rowFieldHelpText') }}
            </template>
          </FormGroup>
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
                v-if="values.table_id"
                v-model="dataSourceFilters"
                :fields="tableFields"
                :filter-type.sync="values.filter_type"
              />
              <p v-if="!values.table_id">
                {{ $t('localBaserowGetRowForm.noTableChosenForFiltering') }}
              </p>
            </Tab>
            <Tab
              :title="$t('localBaserowGetRowForm.searchTabTitle')"
              class="data-source-form__search-form-tab"
            >
              <FormGroup>
                <InjectedFormulaInput
                  v-model="values.search_query"
                  :placeholder="
                    $t('localBaserowGetRowForm.searchFieldPlaceHolder')
                  "
                />
              </FormGroup>
            </Tab>
          </Tabs>
        </div>
      </div>
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import LocalBaserowTableSelector from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableSelector'
import LocalBaserowTableServiceConditionalForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableServiceConditionalForm'
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'

export default {
  components: {
    InjectedFormulaInput,
    LocalBaserowTableSelector,
    LocalBaserowTableServiceConditionalForm,
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
    dataSourceFilters: {
      get() {
        return this.excludeTrashedFields(this.values.filters)
      },
      set(newValue) {
        this.values.filters = newValue
      },
    },
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
     * source filters array), this method will return a new array
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
