<template>
  <div class="form-view__field-wrapper">
    <div class="form-view__field">
      <div class="form-view__field-inner">
        <div class="form-view__field-name">
          {{ field.name }}
        </div>
        <div class="form-view__field-description">
          {{ field.description }}
        </div>
        <component
          :is="getFieldComponent()"
          :key="field.field.id"
          ref="field"
          :group-id="0"
          :slug="slug"
          :field="field.field"
          :value="value"
          :read-only="false"
          :required="field.required"
          :touched="field._.touched"
          v-bind="getFieldComponentProperties()"
          @update="$emit('input', $event)"
          @touched="field._.touched = true"
        />
      </div>
    </div>
  </div>
</template>

<script>
import FieldContext from '@baserow/modules/database/components/field/FieldContext'

export default {
  name: 'FormPageField',
  components: { FieldContext },
  props: {
    slug: {
      type: String,
      required: true,
    },
    value: {
      required: true,
      validator: () => true,
    },
    field: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getFieldComponent() {
      return this.$registry
        .get('field', this.field.field.type)
        .getFormViewFieldComponent()
    },
    getFieldComponentProperties() {
      return this.$registry
        .get('field', this.field.field.type)
        .getFormViewFieldComponentProperties(this)
    },
    focus() {
      this.$el.scrollIntoView({ behavior: 'smooth' })
      this.$emit('focussed')
    },
    isValid() {
      return this.$refs.field.isValid()
    },
  },
}
</script>
