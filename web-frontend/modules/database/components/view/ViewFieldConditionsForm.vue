<template>
  <div>
    <!--
      Here we use the index as key to avoid loosing focus when filter id change.
    -->
    <div
      v-for="(filter, index) in filters"
      :key="index"
      class="filters__item"
      :class="{
        'filters__item--loading': filter._ && filter._.loading,
      }"
    >
      <a
        v-if="!disableFilter"
        class="filters__remove"
        @click="deleteFilter($event, filter)"
      >
        <i class="fas fa-times"></i>
      </a>
      <span v-else class="filters__remove"></span>
      <div class="filters__operator">
        <span v-if="index === 0">{{ $t('viewFilterContext.where') }}</span>
        <Dropdown
          v-if="index === 1 && !disableFilter"
          :value="filterType"
          :show-search="false"
          class="dropdown--floating dropdown--tiny"
          @input="selectBooleanOperator($event)"
        >
          <DropdownItem
            :name="$t('viewFilterContext.and')"
            value="AND"
          ></DropdownItem>
          <DropdownItem
            :name="$t('viewFilterContext.or')"
            value="OR"
          ></DropdownItem>
        </Dropdown>
        <span v-if="index > 1 || (index > 0 && disableFilter)">
          {{
            filterType === 'AND'
              ? $t('viewFilterContext.and')
              : $t('viewFilterContext.or')
          }}
        </span>
      </div>
      <div class="filters__field">
        <Dropdown
          :value="filter.field"
          :disabled="disableFilter"
          class="dropdown--floating dropdown--tiny"
          @input="updateFilter(filter, { field: $event })"
        >
          <DropdownItem
            v-for="field in fields"
            :key="'field-' + field.id"
            :name="field.name"
            :value="field.id"
            :disabled="!hasCompatibleFilterTypes(field, filterTypes)"
          ></DropdownItem>
        </Dropdown>
      </div>
      <div class="filters__type">
        <Dropdown
          :disabled="disableFilter"
          :value="filter.type"
          class="dropdown--floating dropdown--tiny"
          @input="updateFilter(filter, { type: $event })"
        >
          <DropdownItem
            v-for="fType in allowedFilters(filterTypes, fields, filter.field)"
            :key="fType.type"
            :name="fType.getName()"
            :value="fType.type"
          ></DropdownItem>
        </Dropdown>
      </div>
      <div class="filters__value">
        <component
          :is="getInputComponent(filter.type, filter.field)"
          v-if="
            fieldIdExists(fields, filter.field) &&
            fieldIsCompatible(filter.type, filter.field)
          "
          :ref="`filter-value-${index}`"
          :filter="filter"
          :view="view"
          :fields="fields"
          :disabled="disableFilter"
          :read-only="readOnly"
          @input="updateFilter(filter, { value: $event })"
        />
        <i
          v-else-if="!fieldIdExists(fields, filter.field)"
          v-tooltip="$t('viewFilterContext.relatedFieldNotFound')"
          class="fas fa-exclamation-triangle color-error"
        ></i>
        <i
          v-else-if="!fieldIsCompatible(filter.type, filter.field)"
          v-tooltip="$t('viewFilterContext.filterTypeNotFound')"
          class="fas fa-exclamation-triangle color-error"
        ></i>
      </div>
    </div>
  </div>
</template>

<script>
import { hasCompatibleFilterTypes } from '@baserow/modules/database/utils/field'

export default {
  name: 'ViewFieldConditionsForm',
  props: {
    filters: {
      type: Array,
      required: true,
    },
    disableFilter: {
      type: Boolean,
      required: true,
    },
    filterType: {
      type: String,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    filterTypes() {
      return this.$registry.getAll('viewFilter')
    },
    localFilters() {
      // Copy the filters
      return [...this.filters]
    },
  },
  watch: {
    /**
     * When a filter has been created or removed we want to focus on last value. By
     * watching localFilters instead of filters, the new and old values are differents.
     */
    localFilters(value, old) {
      if (value.length !== old.length) {
        this.$nextTick(() => {
          this.focusValue(value.length - 1)
        })
      }
    },
  },
  methods: {
    hasCompatibleFilterTypes,
    focusValue(position) {
      const ref = `filter-value-${position}`
      if (
        position >= 0 &&
        Object.prototype.hasOwnProperty.call(this.$refs, ref) &&
        this.$refs[ref][0] &&
        Object.prototype.hasOwnProperty.call(this.$refs[ref][0], 'focus')
      ) {
        this.$refs[ref][0].focus()
      }
    },
    /**
     * Returns a list of filter types that are allowed for the given fieldId.
     */
    allowedFilters(filterTypes, fields, fieldId) {
      const field = fields.find((f) => f.id === fieldId)
      return Object.values(filterTypes).filter((filterType) => {
        return field !== undefined && filterType.fieldIsCompatible(field)
      })
    },
    deleteFilter(event, filter) {
      event.deletedFilterEvent = true
      this.$emit('deleteFilter', filter)
    },
    /**
     * Updates a filter with the given values. Some data manipulation will also be done
     * because some filter types are not compatible with certain field types.
     */
    updateFilter(filter, values) {
      const fieldId = Object.prototype.hasOwnProperty.call(values, 'field')
        ? values.field
        : filter.field
      const type = Object.prototype.hasOwnProperty.call(values, 'type')
        ? values.type
        : filter.type
      const value = Object.prototype.hasOwnProperty.call(values, 'value')
        ? values.value
        : filter.value

      // If the field has changed we need to check if the filter type is compatible
      // and if not we are going to choose the first compatible type.
      if (Object.prototype.hasOwnProperty.call(values, 'field')) {
        const allowedFilterTypes = this.allowedFilters(
          this.filterTypes,
          this.fields,
          fieldId
        ).map((filter) => filter.type)
        if (!allowedFilterTypes.includes(type)) {
          values.type = allowedFilterTypes[0]
        }
      }

      // If the type or value has changed it could be that the value needs to be
      // formatted or prepared.
      if (
        Object.prototype.hasOwnProperty.call(values, 'field') ||
        Object.prototype.hasOwnProperty.call(values, 'type') ||
        Object.prototype.hasOwnProperty.call(values, 'value')
      ) {
        const filterType = this.$registry.get('viewFilter', type)
        const field = this.fields.find(({ id }) => id === fieldId)
        values.value = filterType.prepareValue(value, field, true)
      }

      this.$emit('updateFilter', { filter, values })
    },
    selectBooleanOperator(value) {
      this.$emit('selectOperator', value)
    },
    /**
     * Returns the input component related to the filter type. This component is
     * responsible for updating the filter value.
     */
    getInputComponent(type, fieldId) {
      const field = this.fields.find(({ id }) => id === fieldId)
      return this.$registry.get('viewFilter', type).getInputComponent(field)
    },
    fieldIdExists(fields, fieldId) {
      return fields.findIndex((field) => field.id === fieldId) !== -1
    },
    fieldIsCompatible(filterType, fieldId) {
      const field = this.fields.find(({ id }) => id === fieldId)
      return this.$registry
        .get('viewFilter', filterType)
        .fieldIsCompatible(field)
    },
  },
}
</script>
