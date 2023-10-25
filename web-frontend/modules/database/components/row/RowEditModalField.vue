<template>
  <div class="control">
    <label class="control__label">
      <a
        :class="{ 'row-modal__field-item-handle': sortable }"
        data-field-handle
      ></a>
      <i class="control__label-icon" :class="field._.type.iconClass"></i>
      {{ field.name }}
      <i
        v-if="!readOnly && canModifyFields"
        ref="contextLink"
        class="control__context baserow-icon-more-vertical"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 0)"
      ></i>
    </label>
    <FieldContext
      ref="context"
      :database="database"
      :table="table"
      :field="field"
      @update="$emit('field-updated', $event)"
      @delete="$emit('field-deleted')"
    >
      <li v-if="canBeHidden">
        <a @click="$emit('toggle-field-visibility', { field })">
          <i
            class="context__menu-icon"
            :class="[hidden ? 'iconoir-eye-empty' : 'iconoir-eye-off']"
          ></i>
          {{ $t(hidden ? 'fieldContext.showField' : 'fieldContext.hideField') }}
        </a>
      </li>
    </FieldContext>
    <component
      :is="getFieldComponent(field.type)"
      ref="field"
      :workspace-id="database.workspace.id"
      :field="field"
      :value="row['field_' + field.id]"
      :read-only="readOnly"
      @update="update"
      @refresh-row="$emit('refresh-row', row)"
    />
  </div>
</template>

<script>
import FieldContext from '@baserow/modules/database/components/field/FieldContext'

export default {
  name: 'RowEditModalField',
  components: { FieldContext },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
    sortable: {
      type: Boolean,
      default: false,
    },
    canModifyFields: {
      type: Boolean,
      required: false,
      default: true,
    },
    canBeHidden: {
      type: Boolean,
      required: false,
      default: true,
    },
    hidden: {
      type: Boolean,
      required: false,
      default: false,
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
      return this.$registry
        .get('field', type)
        .getRowEditFieldComponent(this.field)
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
