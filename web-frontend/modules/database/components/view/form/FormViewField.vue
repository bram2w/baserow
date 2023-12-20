<template>
  <div class="form-view__field-wrapper">
    <div
      class="form-view__field form-view__field--editable"
      :class="{ 'form-view__field--selected': selected }"
      @click="select()"
    >
      <div class="form-view__field-head">
        <a
          v-if="addHandle"
          v-show="!readOnly"
          class="form-view__field-head-handle"
          data-field-handle
        ></a>

        <i
          class="form-view__field-head-icon"
          :class="field._.type.iconClass"
        ></i>

        <div class="form-view__field-head-name">{{ field.name }}</div>
        <a
          v-if="!readOnly"
          v-tooltip="'Remove field'"
          class="form-view__field-head-hide"
          @click="$emit('hide', field)"
        >
          <i class="iconoir-eye-off"></i>
        </a>
      </div>
      <div class="form-view__field-inner">
        <div class="form-view__field-name">
          <Editable
            ref="name"
            :value="fieldOptions.name || field.name"
            @change="$emit('updated-field-options', { name: $event.value })"
            @editing="editingName = $event"
          ></Editable>
          <a
            v-if="!readOnly"
            class="form-view__edit form-view-field-edit"
            :class="{ 'form-view__edit--hidden': editingName }"
            @click="$refs.name.edit()"
          >
            <i class="form-view__edit-icon iconoir-edit-pencil"></i>
          </a>
        </div>
        <div class="form-view__field-description">
          <Editable
            ref="description"
            :value="fieldOptions.description"
            :placeholder="$t('formViewField.descriptionPlaceholder')"
            :multiline="true"
            @change="
              $emit('updated-field-options', { description: $event.value })
            "
            @editing="editingDescription = $event"
          ></Editable>
          <a
            v-if="!readOnly"
            class="form-view__edit form-view-field-edit"
            :class="{ 'form-view__edit--hidden': editingDescription }"
            @click="$refs.description.edit()"
          >
            <i class="form-view__edit-icon iconoir-edit-pencil"></i
          ></a>
        </div>
        <component
          :is="selectedFieldComponent.component"
          ref="field"
          :slug="view.slug"
          :workspace-id="database.workspace.id"
          :field="field"
          :value="value"
          :read-only="readOnly"
          :lazy-load="true"
          :touched="false"
          :required="fieldOptions.required"
          @update="updateValue"
        />
        <div class="form-view__field-options">
          <div
            v-if="Object.keys(fieldComponents).length > 1"
            class="control control--horizontal-variable"
          >
            <label class="control__label">
              {{ $t('formViewField.showFieldAs') }}
            </label>
            <div class="control__elements">
              <RadioButton
                v-for="(v, key) in fieldComponents"
                :key="key"
                :model-value="fieldOptions.field_component"
                :value="key"
                :disabled="readOnly"
                class="margin-right-1"
                @input="
                  $emit('updated-field-options', { field_component: $event })
                "
                >{{ v.name }}</RadioButton
              >
            </div>
          </div>
          <SwitchInput
            :value="fieldOptions.required"
            :disabled="readOnly"
            @input="$emit('updated-field-options', { required: $event })"
            >{{ $t('formViewField.required') }}</SwitchInput
          >
          <SwitchInput
            v-if="allowedConditionalFields.length > 0"
            :value="fieldOptions.show_when_matching_conditions"
            :disabled="readOnly"
            @input="setShowWhenMatchingConditions($event)"
            >{{ $t('formViewField.showWhenMatchingConditions') }}</SwitchInput
          >
          <div
            v-if="
              allowedConditionalFields.length > 0 &&
              fieldOptions.show_when_matching_conditions
            "
            class="form-view__conditions"
          >
            <ViewFieldConditionsForm
              :filters="fieldOptions.conditions"
              :filter-groups="fieldOptions.condition_groups"
              :disable-filter="readOnly"
              :filter-type="fieldOptions.condition_type"
              :view="view"
              :fields="allowedConditionalFields"
              :read-only="readOnly"
              :full-width="true"
              :variant="'dark'"
              :sorted="true"
              @addFilter="addCondition(fieldOptions, $event)"
              @deleteFilter="deleteCondition(fieldOptions, $event)"
              @updateFilter="updateCondition(fieldOptions, $event)"
              @selectOperator="
                $emit('updated-field-options', { condition_type: $event })
              "
              @deleteFilterGroup="deleteConditionGroup(fieldOptions, $event)"
              @selectFilterGroupOperator="
                updateConditionGroupOperator(fieldOptions, $event)
              "
              @filterFocused="
                $store.dispatch('view/setFocusFilter', { view, filterId: null })
              "
            />
            <div class="form-view__condition-actions">
              <a
                class="form-view__add-condition"
                @click="addCondition(fieldOptions)"
              >
                <i class="iconoir-plus"></i>
                {{ $t('formViewField.addCondition') }}
              </a>
              <a
                class="form-view__add-condition"
                @click="addConditionGroup(fieldOptions)"
              >
                <i class="iconoir-plus"></i>
                {{ $t('formViewField.addConditionGroup') }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { isElement, onClickOutside } from '@baserow/modules/core/utils/dom'
import { clone } from '@baserow/modules/core/utils/object'
import { DEFAULT_FORM_VIEW_FIELD_COMPONENT_KEY } from '@baserow/modules/database/constants'
import FieldContext from '@baserow/modules/database/components/field/FieldContext'
import ViewFieldConditionsForm from '@baserow/modules/database/components/view/ViewFieldConditionsForm'

export default {
  name: 'FormViewField',
  components: { FieldContext, ViewFieldConditionsForm },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    fieldOptions: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    addHandle: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      selected: false,
      editingName: false,
      editingDescription: false,
      value: null,
      movedToBodyChildren: [],
    }
  },
  computed: {
    allowedConditionalFields() {
      const index = this.fields.findIndex((f) => f.id === this.field.id)
      return this.fields.slice(0, index)
    },
    fieldComponents() {
      return this.getFieldType().getFormViewFieldComponents(this.field, this)
    },
    selectedFieldComponent() {
      const components = this.fieldComponents
      return Object.prototype.hasOwnProperty.call(
        components,
        this.fieldOptions.field_component
      )
        ? components[this.fieldOptions.field_component]
        : components[DEFAULT_FORM_VIEW_FIELD_COMPONENT_KEY]
    },
  },
  watch: {
    field: {
      deep: true,
      handler() {
        this.resetValue()
      },
    },
  },
  created() {
    this.resetValue()
  },
  methods: {
    select() {
      this.selected = true
      this.$el.clickOutsideEventCancel = onClickOutside(
        this.$el,
        (target, event) => {
          if (
            this.selected &&
            // If the event was not related to deleting the filter.
            !event.deletedFilterEvent &&
            // If the event target is related to a child element that has moved to the
            // body using the `moveToBody` mixin.
            !this.movedToBodyChildren.some((child) => {
              return isElement(child.$el, target)
            })
          ) {
            this.unselect()
          }
        }
      )
    },
    unselect() {
      this.selected = false
      this.$el.clickOutsideEventCancel()
    },
    updateValue(value) {
      this.value = value
    },
    getFieldType() {
      return this.$registry.get('field', this.field.type)
    },
    resetValue() {
      this.value = this.getFieldType().getEmptyValue(this.field)
    },
    createConditionGroup() {
      return {
        id: 0,
        filter_type: 'AND',
      }
    },
    generateCompatibleCondition(conditionGroupId = null) {
      const field =
        this.allowedConditionalFields[this.allowedConditionalFields.length - 1]
      const viewFilterTypes = this.$registry.getAll('viewFilter')
      const compatibleType = Object.values(viewFilterTypes).find(
        (viewFilterType) => {
          return viewFilterType.fieldIsCompatible(field)
        }
      )
      const newCondition = {
        id: 0,
        field: field.id,
        type: compatibleType.type,
        value: '',
      }
      if (conditionGroupId !== null) {
        newCondition.group = conditionGroupId
      }
      return newCondition
    },
    setShowWhenMatchingConditions(value) {
      const values = { show_when_matching_conditions: value }
      if (value && this.fieldOptions.conditions.length === 0) {
        values.conditions = [this.generateCompatibleCondition()]
      }
      this.$emit('updated-field-options', values)
    },
    addCondition(
      { conditions, condition_groups: conditionGroups },
      conditionGroupId = null
    ) {
      const newConditions = conditions.slice()
      const newCondition = this.generateCompatibleCondition(conditionGroupId)
      newConditions.push(newCondition)
      this.$emit('updated-field-options', {
        conditions: newConditions,
        condition_groups: conditionGroups,
      })
      this.$store.dispatch('view/setFocusFilter', {
        view: this.view,
        filterId: newCondition.id,
      })
    },
    addConditionGroup({ conditions, condition_groups: filterGroups }) {
      const newConditionGroup = this.createConditionGroup()
      const newConditionGroups = filterGroups.slice()
      newConditionGroups.push(newConditionGroup)

      const newConditions = conditions.slice()
      const newCondition = this.generateCompatibleCondition(
        newConditionGroup.id
      )
      newConditions.push(newCondition)
      this.$emit('updated-field-options', {
        condition_groups: newConditionGroups,
        conditions: newConditions,
      })
      this.$store.dispatch('view/setFocusFilter', {
        view: this.view,
        filterId: newCondition.id,
      })
    },
    updateConditionGroupOperator(
      { conditions, condition_groups: conditioGroups },
      { value, filterGroup }
    ) {
      conditioGroups = clone(conditioGroups.slice())
      conditioGroups.forEach((g, index) => {
        if (g.id === filterGroup.id) {
          Object.assign(conditioGroups[index], { filter_type: value })
        }
      })
      this.$emit('updated-field-options', {
        conditions,
        condition_groups: conditioGroups,
      })
    },
    updateCondition(
      { conditions, condition_groups: conditionGroups },
      condition
    ) {
      conditions = clone(conditions.slice())
      conditions.forEach((c, index) => {
        if (c.id === condition.filter.id) {
          Object.assign(conditions[index], condition.values)
        }
      })
      this.$emit('updated-field-options', {
        conditions,
        condition_groups: conditionGroups,
      })
    },
    deleteCondition(
      { conditions, condition_groups: conditionGroups },
      condition
    ) {
      // We need to wait for the next tick, otherwise the condition is already deleted
      // before the event completes, resulting in a click outside of the field.
      this.$nextTick(() => {
        conditions = conditions.filter((c) => c.id !== condition.id)
        this.$emit('updated-field-options', {
          conditions,
          condition_groups: conditionGroups,
        })
      })
    },
    deleteConditionGroup(
      { conditions, condition_groups: conditionGroups },
      { group }
    ) {
      // We need to wait for the next tick, otherwise the condition is already deleted
      // before the event completes, resulting in a click outside of the field.
      this.$nextTick(() => {
        const conditionIdsToRemove = conditions
          .filter((c) => c.group === group.id)
          .map((c) => c.id)
        conditions = conditions.filter(
          (c) => !conditionIdsToRemove.includes(c.id)
        )
        conditionGroups = conditionGroups.filter((g) => g.id !== group.id)
        this.$emit('updated-field-options', {
          conditions,
          condition_groups: conditionGroups,
        })
      })
    },
    /**
     * This method is called by every child that has moved to the body, using the
     * `moveToBody` mixin. In order to make sure that this component isn't unselected
     * when clicking inside a child that has moved to body component, we add them to an
     * array and check if the event target is actually a child when clicking outside of
     * the element related to this component.
     */
    registerMoveToBodyChild(child) {
      this.movedToBodyChildren.push(child)
    },
  },
}
</script>
