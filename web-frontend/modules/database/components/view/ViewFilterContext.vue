<template>
  <Context
    ref="context"
    class="filters"
    :class="{ 'context--loading-overlay': view._.loading }"
  >
    <div v-show="view.filters.length === 0">
      <div class="filters__none">
        <div class="filters__none-title">You have not yet created a filter</div>
        <div class="filters__none-description">
          Filters allow you to show rows that apply to your conditions.
        </div>
      </div>
    </div>
    <div
      v-for="(filter, index) in view.filters"
      :key="filter.id"
      class="filters__item"
      :class="{
        'filters__item--loading': filter._.loading,
      }"
    >
      <a
        v-if="!readOnly"
        class="filters__remove"
        @click.prevent="deleteFilter(filter)"
      >
        <i class="fas fa-times"></i>
      </a>
      <div class="filters__operator">
        <span v-if="index === 0">Where</span>
        <Dropdown
          v-if="index === 1 && !readOnly"
          :value="view.filter_type"
          :show-search="false"
          class="dropdown--floating dropdown--tiny"
          @input="updateView(view, { filter_type: $event })"
        >
          <DropdownItem name="And" value="AND"></DropdownItem>
          <DropdownItem name="Or" value="OR"></DropdownItem>
        </Dropdown>
        <span
          v-if="
            (index > 1 || (index > 0 && readOnly)) && view.filter_type === 'AND'
          "
          >And</span
        >
        <span
          v-if="
            (index > 1 || (index > 0 && readOnly)) && view.filter_type === 'OR'
          "
          >Or</span
        >
      </div>
      <div class="filters__field">
        <Dropdown
          :value="filter.field"
          :disabled="readOnly"
          class="dropdown--floating dropdown--tiny"
          @input="updateFilter(filter, { field: $event })"
        >
          <DropdownItem
            :key="'filter-field-' + filter.id + '-' + primary.id"
            :name="primary.name"
            :value="primary.id"
            :disabled="hasCompatibleFilterTypes(primary, filterTypes)"
          ></DropdownItem>
          <DropdownItem
            v-for="field in fields"
            :key="'filter-field-' + filter.id + '-' + field.id"
            :name="field.name"
            :value="field.id"
            :disabled="hasCompatibleFilterTypes(field, filterTypes)"
          ></DropdownItem>
        </Dropdown>
      </div>
      <div class="filters__type">
        <Dropdown
          :disabled="readOnly"
          :value="filter.type"
          class="dropdown--floating dropdown--tiny"
          @input="updateFilter(filter, { type: $event })"
        >
          <DropdownItem
            v-for="filterType in allowedFilters(
              filterTypes,
              primary,
              fields,
              filter.field
            )"
            :key="filterType.type"
            :name="filterType.name"
            :value="filterType.type"
          ></DropdownItem>
        </Dropdown>
      </div>
      <div class="filters__value">
        <component
          :is="getInputComponent(filter.type)"
          :ref="'filter-' + filter.id + '-value'"
          :value="filter.value"
          :field-id="filter.field"
          :fields="fields"
          :primary="primary"
          :read-only="readOnly"
          @input="updateFilter(filter, { value: $event })"
        />
      </div>
    </div>
    <div v-if="!readOnly" class="filters_footer">
      <a class="filters__add" @click.prevent="addFilter()">
        <i class="fas fa-plus"></i>
        add filter
      </a>
      <div v-if="view.filters.length > 0">
        <SwitchInput
          :value="view.filters_disabled"
          @input="updateView(view, { filters_disabled: $event })"
          >all disabled</SwitchInput
        >
      </div>
    </div>
  </Context>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'ViewFilterContext',
  mixins: [context],
  props: {
    primary: {
      type: Object,
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
  },
  beforeMount() {
    this.$bus.$on('view-filter-created', this.filterCreated)
  },
  beforeDestroy() {
    this.$bus.$off('view-filter-created', this.filterCreated)
  },
  methods: {
    /**
     * When the filter has been created we want to focus on the value.
     */
    filterCreated({ filter }) {
      this.$nextTick(() => {
        this.focusValue(filter)
      })
    },
    focusValue(filter) {
      const ref = 'filter-' + filter.id + '-value'
      if (
        Object.prototype.hasOwnProperty.call(this.$refs, ref) &&
        Object.prototype.hasOwnProperty.call(this.$refs[ref][0], 'focus')
      ) {
        this.$refs[ref][0].focus()
      }
    },
    /**
     * Indicates if the field has any compatible filter types.
     */
    hasCompatibleFilterTypes(field, filterTypes) {
      for (const type in filterTypes) {
        if (filterTypes[type].compatibleFieldTypes.includes(field.type)) {
          return false
        }
      }
      return true
    },
    /**
     * Returns a list of filter types that are allowed for the given fieldId.
     */
    allowedFilters(filterTypes, primary, fields, fieldId) {
      const field =
        primary.id === fieldId ? primary : fields.find((f) => f.id === fieldId)
      return Object.values(filterTypes).filter((filterType) => {
        return (
          field !== undefined &&
          filterType.compatibleFieldTypes.includes(field.type)
        )
      })
    },
    async addFilter() {
      try {
        const { filter } = await this.$store.dispatch('view/createFilter', {
          view: this.view,
          field: this.primary,
          values: {
            field: this.primary.id,
            value: '',
            emitEvent: false,
          },
        })
        this.$emit('changed')

        // Wait for the filter to be rendered and then focus on the value input.
        this.$nextTick(() => {
          this.focusValue(filter)
        })
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    async deleteFilter(filter) {
      try {
        await this.$store.dispatch('view/deleteFilter', {
          view: this.view,
          filter,
        })
        this.$emit('changed')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    /**
     * Updates a filter with the given values. Some data manipulation will also be done
     * because some filter types are not compatible with certain field types.
     */
    async updateFilter(filter, values) {
      const field = Object.prototype.hasOwnProperty.call(values, 'field')
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
          this.primary,
          this.fields,
          field
        ).map((filter) => filter.type)
        if (!allowedFilterTypes.includes(type)) {
          values.type = allowedFilterTypes[0]
        }
      }

      // If the type or value has changed it could be that the value needs to be
      // formatted or prepared.
      if (
        Object.prototype.hasOwnProperty.call(values, 'type') ||
        Object.prototype.hasOwnProperty.call(values, 'value')
      ) {
        const filterType = this.$registry.get('viewFilter', type)
        values.value = filterType.prepareValue(value)
      }

      try {
        await this.$store.dispatch('view/updateFilter', {
          filter,
          values,
        })
        this.$emit('changed')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    /**
     * Updates the view filter type. It will mark the view as loading because that
     * will also trigger the loading state of the second filter.
     */
    async updateView(view, values) {
      this.$store.dispatch('view/setItemLoading', { view, value: true })

      try {
        await this.$store.dispatch('view/update', {
          view,
          values,
        })
        this.$emit('changed')
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.$store.dispatch('view/setItemLoading', { view, value: false })
    },
    /**
     * Returns the input component related to the filter type. This component is
     * responsible for updating the filter value.
     */
    getInputComponent(type) {
      return this.$registry.get('viewFilter', type).getInputComponent()
    },
  },
}
</script>
