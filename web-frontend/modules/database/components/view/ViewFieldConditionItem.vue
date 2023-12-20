<template>
  <div
    class="filters__condition-item"
    :class="{ 'filters__condition-item--loading': filter._?.loading }"
  >
    <div class="filters__field">
      <Dropdown
        :value="filter.field"
        :disabled="disableFilter"
        :fixed-items="true"
        small
        @input="$emit('updateFilter', { field: $event })"
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
        :fixed-items="true"
        small
        @input="$emit('updateFilter', { type: $event })"
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
        ref="filter-value"
        :filter="filter"
        :view="view"
        :fields="fields"
        :disabled="disableFilter"
        :read-only="readOnly"
        @input="$emit('updateFilter', { value: $event })"
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
    <a
      class="filters__remove"
      :class="{ 'filters__remove--disabled': disableFilter }"
      @click="!disableFilter && $emit('deleteFilter', $event)"
    >
      <i class="iconoir-bin"></i>
    </a>
  </div>
</template>

<script>
import { hasCompatibleFilterTypes } from '@baserow/modules/database/utils/field'
import viewFilterTypes from '@baserow/modules/database/mixins/viewFilterTypes'

export default {
  name: 'ViewFieldConditionItem',
  mixins: [viewFilterTypes],
  props: {
    filter: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: false,
      default: () => {},
    },
    disableFilter: {
      type: Boolean,
      default: false,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    hasCompatibleFilterTypes,
    focusValue() {
      if (this.$refs['filter-value']?.focus !== undefined) {
        this.$refs['filter-value'].focus()
      }
    },
    allowedFilters(filterTypes, fields, fieldId) {
      const field = fields.find((f) => f.id === fieldId)
      return Object.values(filterTypes).filter((filterType) => {
        return field !== undefined && filterType.fieldIsCompatible(field)
      })
    },
    getInputComponent(type, fieldId) {
      const field = this.fields.find(({ id }) => id === fieldId)
      return this.$registry.get('viewFilter', type).getInputComponent(field)
    },
    fieldIdExists(fields, fieldId) {
      return fields.findIndex((field) => field.id === fieldId) !== -1
    },
    fieldIsCompatible(filterType, fieldId) {
      const field = this.fields.find(({ id }) => id === fieldId)
      if (!(filterType in this.filterTypes)) {
        return false
      }
      return this.filterTypes[filterType].fieldIsCompatible(field)
    },
  },
}
</script>
