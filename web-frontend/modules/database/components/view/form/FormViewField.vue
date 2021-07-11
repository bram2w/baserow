<template>
  <div class="form-view__field-wrapper">
    <div
      class="form-view__field form-view__field--editable"
      :class="{ 'form-view__field--selected': selected }"
      @click="select()"
    >
      <div class="form-view__field-head">
        <a
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
            >required</SwitchInput
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { isElement } from '@baserow/modules/core/utils/dom'
import FieldContext from '@baserow/modules/database/components/field/FieldContext'

export default {
  name: 'FormViewField',
  components: { FieldContext },
  props: {
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
    fieldOptions: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      selected: false,
      editingName: false,
      editingDescription: false,
      value: null,
    }
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
      this.$el.clickOutsideEvent = (event) => {
        if (
          this.selected &&
          // If the user not clicked inside the field.
          !isElement(this.$el, event.target)
        ) {
          this.unselect()
        }
      }
      document.body.addEventListener('click', this.$el.clickOutsideEvent)
    },
    unselect() {
      this.selected = false
      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
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
  },
}
</script>
