<template>
  <div
    class="filters__items"
    :class="{
      'filters__container--dark': variant === 'dark',
      'filters__items--full-width': fullWidth,
    }"
  >
    <!--
      Here we use the index as key to avoid loosing focus when filter id change.
    -->
    <div
      v-for="(filter, index) in filtersTree.filters"
      :key="index"
      class="filters__item-wrapper"
    >
      <div class="filters__item filters__item--level-1">
        <ViewFilterFormOperator
          :index="index"
          :filter-type="filterType"
          :disable-filter="disableFilter"
          @select-boolean-operator="$emit('selectOperator', $event)"
        />
        <ViewFieldConditionItem
          :ref="`condition-${filter.id}`"
          :filter="filter"
          :view="view"
          :fields="fields"
          :disable-filter="disableFilter"
          :read-only="readOnly"
          @updateFilter="updateFilter(filter, $event)"
          @deleteFilter="deleteFilter(filter, $event)"
        />
      </div>
    </div>
    <div
      v-for="(groupNode, groupIndex) in filtersTree.groups"
      :key="filtersTree.filters.length + groupIndex"
      class="filters__group-item-wrapper"
    >
      <ViewFilterFormOperator
        :index="filtersTree.filters.length + groupIndex"
        :filter-type="filterType"
        :disable-filter="disableFilter"
        @select-boolean-operator="$emit('selectOperator', $event)"
      />
      <div class="filters__group-item">
        <div class="filters__group-item-filters">
          <div
            v-for="(filter, index) in groupNode.filters"
            :key="`${groupIndex}-${index}`"
            class="filters__item-wrapper"
          >
            <div class="filters__item filters__item--level-2">
              <ViewFilterFormOperator
                :index="index"
                :filter-type="groupNode.group.filter_type"
                :disable-filter="disableFilter"
                @select-boolean-operator="
                  $emit('selectFilterGroupOperator', {
                    value: $event,
                    filterGroup: groupNode.group,
                  })
                "
              />
              <ViewFieldConditionItem
                :ref="`condition-${filter.id}`"
                :filter="filter"
                :view="view"
                :fields="fields"
                :disable-filter="disableFilter"
                :read-only="readOnly"
                @updateFilter="updateFilter(filter, $event)"
                @deleteFilter="deleteFilter(filter, $event)"
              />
            </div>
          </div>
        </div>
        <div v-if="!disableFilter" class="filters__group-item-actions">
          <a
            class="filters__add"
            @click.prevent="$emit('addFilter', groupNode.group.id)"
          >
            <i class="filters__add-icon iconoir-plus"></i>
            {{ addConditionLabel }}</a
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ViewFilterFormOperator from '@baserow/modules/database/components/view/ViewFilterFormOperator'
import ViewFieldConditionItem from '@baserow/modules/database/components/view/ViewFieldConditionItem'

const GroupNode = class {
  constructor(group, parent = null) {
    this.group = group
    this.parent = parent
    this.groups = []
    this.filters = []
    if (parent) {
      parent.groups.push(this)
    }
  }

  findGroup(id) {
    if (this.group && this.group.id === id) {
      return this
    }
    for (const group of this.groups) {
      const found = group.findGroup(id)
      if (found) {
        return found
      }
    }
    return null
  }

  addFilter(filter) {
    this.filters.push(filter)
  }

  remove() {
    if (this.parent) {
      this.parent.groups = this.parent.groups.filter((g) => g !== this)
    }
  }
}

export default {
  name: 'ViewFieldConditionsForm',
  components: {
    ViewFilterFormOperator,
    ViewFieldConditionItem,
  },
  props: {
    filters: {
      type: Array,
      required: true,
    },
    filterGroups: {
      type: Array,
      required: false,
      default: () => [],
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
    addConditionString: {
      type: String,
      required: false,
      default: null,
    },
    variant: {
      type: String,
      required: false,
      default: 'light',
    },
    fullWidth: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      groups: {},
    }
  },
  computed: {
    addConditionLabel() {
      return (
        this.addConditionString ||
        this.$t('viewFieldConditionsForm.addCondition')
      )
    },
    filterTypes() {
      return this.$registry.getAll('viewFilter')
    },
    localFilters() {
      // Copy the filters
      return [...this.filters]
    },
    filtersTree() {
      const root = new GroupNode(null)
      const groups = { '': root }
      for (const filterGroup of this.filterGroups) {
        const parentId = filterGroup.parent || ''
        const parent = groups[parentId]
        const node = new GroupNode(filterGroup, parent)
        groups[filterGroup.id] = node
      }
      for (const filter of this.filters) {
        const groupId = filter.group != null ? filter.group : ''
        const group = groups[groupId]
        if (group) {
          group.addFilter(filter)
        }
      }
      return root
    },
  },
  watch: {
    /**
     * When a filter has been created or removed we want to focus on last value. By
     * watching localFilters instead of filters, the new and old values are different.
     */
    localFilters(value, old) {
      if (value.length !== old.length && value.length > 0) {
        this.$nextTick(() => {
          this.focusFilterValue(value[value.length - 1])
        })
      }
    },
  },
  methods: {
    focusFilterValue(filter) {
      const ref = `condition-${filter.id}`
      if (this.$refs[ref] && this.$refs[ref].length > 0) {
        this.$refs[ref][0]?.focusValue()
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
    deleteFilter(filter, event) {
      event.deletedFilterEvent = true
      const groupNode = this.filtersTree.findGroup(filter.group)
      const lastInGroup = groupNode && groupNode.filters.length === 1
      if (lastInGroup) {
        this.$emit('deleteFilterGroup', groupNode)
      } else {
        this.$emit('deleteFilter', filter)
      }
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
  },
}
</script>
