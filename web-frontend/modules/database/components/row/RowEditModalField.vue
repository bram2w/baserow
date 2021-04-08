<template>
  <div class="control">
    <label class="control__label">
      <i
        class="fas control__label-icon"
        :class="'fa-' + field._.type.iconClass"
      ></i>
      {{ field.name }}
      <a
        v-if="!readOnly"
        ref="contextLink"
        class="control__context"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 0)"
      >
        <i class="fas fa-caret-down"></i>
      </a>
    </label>
    <FieldContext
      ref="context"
      :table="table"
      :field="field"
      @update="$emit('field-updated', $event)"
      @delete="$emit('field-deleted')"
    ></FieldContext>
    <component
      :is="getFieldComponent(field.type)"
      ref="field"
      :field="field"
      :value="row['field_' + field.id]"
      :read-only="readOnly"
      @update="update"
    />
  </div>
</template>

<script>
import FieldContext from '@baserow/modules/database/components/field/FieldContext'

export default {
  name: 'RowEditModalField',
  components: { FieldContext },
  props: {
    table: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    getFieldComponent(type) {
      return this.$registry.get('field', type).getRowEditFieldComponent()
    },
    update(value, oldValue) {
      this.$emit('update', {
        row: this.row,
        field: this.field,
        value,
        oldValue,
      })
    },
  },
}
</script>
