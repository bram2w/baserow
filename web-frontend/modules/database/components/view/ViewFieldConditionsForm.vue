<template>
  <div
    class="filters__items"
    :class="{
      'filters__container--dark': variant === 'dark',
      'filters__items--full-width': fullWidth,
    }"
  >
    <div
      v-for="(filter, index) in filtersTree.filtersOrdered()"
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
          :is-public-view="isPublicView"
          :fields="fields"
          :disable-filter="disableFilter"
          :read-only="readOnly"
          @updateFilter="updateFilter(filter, $event)"
          @deleteFilter="deleteFilter(filter, $event)"
        >
          <template #filterInputComponent="{ slotProps }">
            <slot name="filterInputComponent" :slot-props="slotProps"></slot>
          </template>
          <template #afterValueInput="{ slotProps }">
            <slot name="afterValueInput" :slot-props="slotProps"></slot>
          </template>
        </ViewFieldConditionItem>
      </div>
    </div>
    <div
      v-for="(groupNode, groupIndex) in filtersTree.groupsOrdered()"
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
            v-for="(filter, index) in groupNode.filtersOrdered()"
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
                :is-public-view="isPublicView"
                :fields="fields"
                :disable-filter="disableFilter"
                :read-only="readOnly"
                @updateFilter="updateFilter(filter, $event)"
                @deleteFilter="deleteFilter(filter, $event)"
              >
                <template #filterInputComponent="{ slotProps }">
                  <slot
                    name="filterInputComponent"
                    :slot-props="slotProps"
                  ></slot>
                </template>
                <template #afterValueInput="{ slotProps }">
                  <slot name="afterValueInput" :slot-props="slotProps"></slot>
                </template>
              </ViewFieldConditionItem>
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
import { sortNumbersAndUuid1Asc } from '@baserow/modules/core/utils/sort'

const GroupNode = class {
  constructor(group, parent = null, sorted = false) {
    this.group = group
    this.parent = parent
    this.children = []
    this.filters = []
    this.sorted = sorted
    if (parent) {
      parent.children.push(this)
    }
  }

  groupsOrdered() {
    if (this.sorted) {
      return this.children
    }

    return this.children.sort((a, b) => {
      return sortNumbersAndUuid1Asc(a.group, b.group)
    })
  }

  filtersOrdered() {
    if (this.sorted) {
      return this.filters
    }

    return this.filters.sort(sortNumbersAndUuid1Asc)
  }

  findGroup(id) {
    if (this.group && this.group.id === id) {
      return this
    }
    for (const groupNode of this.children) {
      const found = groupNode.findGroup(id)
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
      this.parent.children = this.parent.children.filter((g) => g !== this)
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
    // A view is optional, but may be required by some specific
    // field components, such as `ViewFilterTypeLinkRow`.
    view: {
      type: Object,
      required: false,
      default: () => {},
    },
    isPublicView: {
      type: Boolean,
      required: false,
      default: false,
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
    sorted: {
      type: Boolean,
      required: false,
      default: false,
    },
    /*
     * Allows the parent component to provide a function that will be called
     * when a filter is updated. This is useful for components that need to
     * do additional processing when a filter is updated.
     */
    prepareValue: {
      type: Function,
      required: false,
      default: (value, filter, field, filterType) => {
        return filterType.prepareValue(value, field, true)
      },
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
    filtersTree() {
      const root = new GroupNode(null, null, this.sorted)
      const groups = { '': root }
      for (const filterGroup of this.filterGroups) {
        const parentId = filterGroup.parent || ''
        const parent = groups[parentId]
        const node = new GroupNode(filterGroup, parent, this.sorted)
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
    'view._.focusFilter': {
      handler(filterId) {
        const filter =
          filterId !== null && this.filters.find((f) => f.id === filterId)
        if (filter) {
          this.focusFilterValue(filter)
        }
      },
      immediate: true,
    },
  },
  methods: {
    focusFilterValue(filter) {
      this.$nextTick(() => {
        const ref = `condition-${filter.id}`
        if (this.$refs[ref] && this.$refs[ref].length > 0) {
          this.$refs[ref][0]?.focusValue()
        }
        this.$emit('filterFocused', filter)
      })
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

        values.value = this.prepareValue(value, filter, field, filterType)
      }

      this.$emit('updateFilter', { filter, values })
    },
  },
}
</script>
