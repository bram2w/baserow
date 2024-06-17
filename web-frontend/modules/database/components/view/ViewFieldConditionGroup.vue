<!-- eslint-disable vue/no-multiple-template-root -->
<template>
  <div class="filters__group-item">
    <div v-if="groupNode.filters.length" class="filters__group-item-filters">
      <div
        v-for="(filter, filterIndex) in groupNode.filtersOrdered()"
        :key="filterIndex"
        class="filters__item-wrapper"
      >
        <div class="filters__item filters__item--level-2">
          <ViewFilterFormOperator
            :index="filterIndex"
            :filter-type="groupNode.group.filter_type"
            :disable-filter="disableFilter"
            @updateFilterType="
              $emit('updateFilterType', {
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
            @updateFilter="$emit('updateFilter', { filter, values: $event })"
            @deleteFilter="$emit('deleteFilter', { filter, event: $event })"
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
    </div>
    <div
      v-for="(subGroupNode, subGroupIndex) in groupNode.children"
      :key="groupNode.filters.length + subGroupIndex"
      class="filters__group-item-wrapper filters__group-item-wrapper--inner"
    >
      <ViewFilterFormOperator
        :index="groupNode.filters.length + subGroupIndex"
        :filter-type="groupNode.group.filter_type"
        :disable-filter="disableFilter"
        @updateFilterType="
          $emit('updateFilterType', {
            value: $event,
            filterGroup: groupNode.group,
          })
        "
      />
      <ViewFieldConditionGroup
        :group-node="subGroupNode"
        :disable-filter="disableFilter"
        :is-public-view="isPublicView"
        :read-only="readOnly"
        :fields="fields"
        :view="view"
        :can-add-filter-groups="false"
        :add-condition-string="addConditionString"
        :add-condition-group-string="addConditionGroupString"
        @addFilter="$emit('addFilter', $event)"
        @addFilterGroup="$emit('addFilterGroup', $event)"
        @updateFilter="$emit('updateFilter', $event)"
        @deleteFilter="$emit('deleteFilter', $event)"
        @updateFilterType="$emit('updateFilterType', $event)"
      >
      </ViewFieldConditionGroup>
    </div>
    <div v-if="!disableFilter" class="filters__group-item-actions">
      <ButtonText
        class="filters__group-item-action--add-filter"
        icon="iconoir-plus"
        @click.prevent="
          $emit('addFilter', { filterGroupId: groupNode.group.id })
        "
      >
        {{ addConditionLabel }}</ButtonText
      >
      <ButtonText
        v-if="canAddFilterGroups"
        class="filters__group-item-action--add-filter-group"
        icon="iconoir-plus"
        @click.prevent="
          $emit('addFilterGroup', {
            filterGroupId: uuidv1(),
            parentGroupId: groupNode.group.id,
          })
        "
      >
        {{ addConditionGroupLabel }}</ButtonText
      >
    </div>
  </div>
</template>

<script>
import { v1 as uuidv1 } from 'uuid'
import ViewFilterFormOperator from '@baserow/modules/database/components/view/ViewFilterFormOperator'
import ViewFieldConditionItem from '@baserow/modules/database/components/view/ViewFieldConditionItem'

export default {
  name: 'ViewFieldConditionGroup',
  components: {
    ViewFilterFormOperator,
    ViewFieldConditionItem,
  },
  props: {
    view: {
      type: Object,
      required: true,
    },
    groupNode: {
      type: Object,
      required: true,
    },
    disableFilter: {
      type: Boolean,
      required: false,
      default: false,
    },
    isPublicView: {
      type: Boolean,
      required: false,
      default: false,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
    fields: {
      type: Array,
      required: true,
    },
    addConditionString: {
      type: String,
      required: false,
      default: null,
    },
    addConditionGroupString: {
      type: String,
      required: false,
      default: null,
    },
    canAddFilterGroups: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  computed: {
    addConditionLabel() {
      return (
        this.addConditionString ||
        this.$t('viewFieldConditionsForm.addCondition')
      )
    },
    addConditionGroupLabel() {
      return (
        this.addConditionGroupString ||
        this.$t('viewFieldConditionsForm.addConditionGroup')
      )
    },
  },
  methods: {
    uuidv1,
  },
}
</script>
