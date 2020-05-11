<template>
  <div class="control">
    <label class="control-label">
      <i
        class="fas control-label-icon"
        :class="'fa-' + field._.type.iconClass"
      ></i>
      {{ field.name }}
      <a
        ref="contextLink"
        class="control-context"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 0)"
      >
        <i class="fas fa-caret-down"></i>
      </a>
    </label>
    <FieldContext ref="context" :field="field"></FieldContext>
    <component
      :is="getFieldComponent(field.type)"
      ref="field"
      :field="field"
      :value="row['field_' + field.id]"
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
    field: {
      type: Object,
      required: true,
    },
    row: {
      type: Object,
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
