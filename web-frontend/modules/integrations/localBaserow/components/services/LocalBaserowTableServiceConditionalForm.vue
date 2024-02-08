<template>
  <div v-if="value">
    <div v-if="value.length === 0">
      <div class="filters__none">
        <div class="filters__none-title">
          {{ $t('localBaserowTableServiceConditionalForm.noFilterTitle') }}
        </div>
        <div class="filters__none-description">
          {{ $t('localBaserowTableServiceConditionalForm.noFilterText') }}
        </div>
      </div>
    </div>
    <ViewFieldConditionsForm
      :filters="getSortedDataSourceFilters()"
      :disable-filter="false"
      :filter-type="filterType"
      :fields="dataSourceFields"
      :read-only="false"
      class="filters__items"
      @deleteFilter="deleteFilter($event)"
      @updateFilter="updateFilter($event)"
      @selectOperator="$emit('update:filterType', $event)"
    >
      <template #filterInputComponent="{ slotProps }">
        <slot name="filterInputComponent" :slot-props="slotProps"></slot>
      </template>
    </ViewFieldConditionsForm>
    <div class="filters_footer">
      <a v-if="!tableLoading" class="filters__add" @click.prevent="addFilter()">
        <i class="filters__add-icon iconoir-plus"></i>
        {{ $t('localBaserowTableServiceConditionalForm.addFilter') }}</a
      >
    </div>
  </div>
</template>

<script>
import ViewFieldConditionsForm from '@baserow/modules/database/components/view/ViewFieldConditionsForm.vue'
import { hasCompatibleFilterTypes } from '@baserow/modules/database/utils/field'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { v1 as uuidv1 } from 'uuid'

export default {
  name: 'LocalBaserowTableServiceConditionalForm',
  components: {
    ViewFieldConditionsForm,
  },
  props: {
    value: {
      type: Array,
      required: true,
    },
    schema: {
      type: Object,
      required: true,
    },
    filterType: {
      type: String,
      required: true,
    },
    tableLoading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    filterTypes() {
      return this.$registry.getAll('viewFilter')
    },
    /*
     * Responsible for finding all field metadata in the schema.
     * This will be used by the `ViewFieldConditionsForm` component
     * to display the filters applicable for each field type.
     */
    dataSourceFields() {
      if (this.schema === null) {
        return []
      }
      const schemaProperties =
        this.schema.type === 'array'
          ? this.schema.items.properties
          : this.schema.properties
      return Object.values(schemaProperties)
        .filter(({ metadata }) => metadata)
        .map((prop) => prop.metadata)
    },
  },
  methods: {
    /*
     * Responsible for returning the first compatible field we have in
     * our schema fields. Used by `addFilter` to decide what the newly
     * added filter's field should be.
     */
    getFirstCompatibleField(fields) {
      return fields
        .slice()
        .sort((a, b) => b.primary - a.primary)
        .find((field) => hasCompatibleFilterTypes(field, this.filterTypes))
    },
    /*
     * Responsible for returning all current data source filters, but
     * sorted by their `order`. Without the sorting, `ViewFieldConditionsForm`
     * will add/update them in a haphazard way.
     */
    getSortedDataSourceFilters() {
      const dataSourceFilters = [...this.value]
      return dataSourceFilters.sort((a, b) => a.order - b.order)
    },
    /*
     * Responsible for asynchronously adding a new data source filter.
     * By default it'll be for the first compatible field, of type equal,
     * and value blank.
     */
    async addFilter() {
      try {
        const field = this.getFirstCompatibleField(this.dataSourceFields)
        if (field === undefined) {
          await this.$store.dispatch('toast/error', {
            title: this.$t(
              'localBaserowTableServiceConditionalForm.noCompatibleFilterTypesErrorTitle'
            ),
            message: this.$t(
              'localBaserowTableServiceConditionalForm.noCompatibleFilterTypesErrorMessage'
            ),
          })
        } else {
          const newFilters = [...this.value]
          // Setting an `id` of `uuidv1` is necessary for two reasons:
          // 1) So that we can distinguish between filters locally
          // 2) It has to match what is sorted against `sortNumbersAndUuid1Asc`.
          newFilters.push({
            id: uuidv1(),
            field: field.id,
            type: 'equal',
            value: '',
          })
          this.$emit('input', newFilters)
        }
      } catch (error) {
        notifyIf(error, 'dataSource')
      }
    },
    /*
     * Responsible for removing the chosen filter from the data source's filters.
     */
    deleteFilter(filter) {
      const newFilters = this.value.filter(({ id }) => {
        return id !== filter.id
      })
      this.$emit('input', newFilters)
    },
    /*
     * Responsible for updating the chosen filter in the data source's filters.
     */
    updateFilter({ filter, values }) {
      const newFilters = this.value.map((filterConf) => {
        if (filterConf.id === filter.id) {
          return { ...filterConf, ...values }
        }
        return filterConf
      })
      this.$emit('input', newFilters)
    },
  },
}
</script>
