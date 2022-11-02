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
        <div class="form-view__field-head-icon">
          <i class="fas fa-fw" :class="'fa-' + field._.type.iconClass"></i>
        </div>
        <div class="form-view__field-head-name">{{ field.name }}</div>
        <a
          v-if="!readOnly"
          v-tooltip="'Remove field'"
          class="form-view__field-head-hide"
          @click="$emit('hide', field)"
        >
          <i class="fas fa-eye-slash"></i>
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
          ></a>
        </div>
        <div class="form-view__field-description">
          <Editable
            ref="description"
            :value="fieldOptions.description"
            :placeholder="$t('formViewField.descriptionPlaceholder')"
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
          ></a>
        </div>
        <component
          :is="getFieldComponent()"
          ref="field"
          :slug="view.slug"
          :group-id="database.group.id"
          :field="field"
          :value="value"
          :read-only="readOnly"
          :lazy-load="true"
          @update="updateValue"
        />
        <div class="form-view__field-options">
          <SwitchInput
            :value="fieldOptions.required"
            :large="true"
            :disabled="readOnly"
            @input="$emit('updated-field-options', { required: $event })"
            >{{ $t('formViewField.required') }}</SwitchInput
          >
          <SwitchInput
            v-if="allowedConditionalFields.length > 0"
            :value="fieldOptions.show_when_matching_conditions"
            :large="true"
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
              :disable-filter="readOnly"
              :filter-type="fieldOptions.condition_type"
              :view="view"
              :fields="allowedConditionalFields"
              :read-only="readOnly"
              @deleteFilter="deleteCondition(fieldOptions.conditions, $event)"
              @updateFilter="updateCondition(fieldOptions.conditions, $event)"
              @selectOperator="
                $emit('updated-field-options', { condition_type: $event })
              "
            />
            <a
              class="form-view__add-condition"
              @click="addCondition(fieldOptions.conditions)"
            >
              <i class="fas fa-plus"></i>
              {{ $t('formViewField.addCondition') }}
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { isElement, onClickOutside } from '@baserow/modules/core/utils/dom'
import { clone } from '@baserow/modules/core/utils/object'
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
    getFieldComponent() {
      return this.getFieldType().getFormViewFieldComponent()
    },
    resetValue() {
      this.value = this.getFieldType().getEmptyValue(this.field)
    },
    generateCompatibleCondition() {
      const field =
        this.allowedConditionalFields[this.allowedConditionalFields.length - 1]
      const viewFilterTypes = this.$registry.getAll('viewFilter')
      const compatibleType = Object.values(viewFilterTypes).find(
        (viewFilterType) => {
          return viewFilterType.fieldIsCompatible(field)
        }
      )
      return {
        id: 0,
        field: field.id,
        type: compatibleType.type,
        value: '',
      }
    },
    setShowWhenMatchingConditions(value) {
      const values = { show_when_matching_conditions: value }
      if (value && this.fieldOptions.conditions.length === 0) {
        values.conditions = [this.generateCompatibleCondition()]
      }
      this.$emit('updated-field-options', values)
    },
    addCondition(conditions) {
      const newConditions = conditions.slice()
      newConditions.push(this.generateCompatibleCondition())
      this.$emit('updated-field-options', { conditions: newConditions })
    },
    updateCondition(conditions, condition) {
      conditions = clone(conditions.slice())
      conditions.forEach((c, index) => {
        if (c.id === condition.filter.id) {
          Object.assign(conditions[index], condition.values)
        }
      })
      this.$emit('updated-field-options', { conditions })
    },
    deleteCondition(conditions, condition) {
      // We need to wait for the next tick, otherwise the condition is already deleted
      // before the event completes, resulting in a click outside of the field.
      this.$nextTick(() => {
        conditions = conditions.filter((c) => c.id !== condition.id)
        this.$emit('updated-field-options', { conditions })
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
