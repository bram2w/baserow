<template>
  <ul class="row-modal__field-list margin-bottom-0">
    <li
      v-for="field in fields"
      :key="'row-edit-field-' + field.id"
      v-sortable="{
        enabled: fieldIsSortable(field),
        id: field.id,
        update: (newOrder) => {
          $emit('order-fields', { newOrder })
        },
        handle: '[data-field-handle]',
        marginTop: -10,
      }"
      class="row-modal__field-item"
    >
      <RowEditModalField
        :ref="'field-' + field.id"
        :field="field"
        :sortable="fieldIsSortable(field)"
        :can-be-hidden="field.primary ? primaryIsSortable : true"
        :hidden="hidden"
        :read-only="readOnly"
        :row="row"
        :table="table"
        :database="database"
        :can-modify-fields="canModifyFields"
        @field-updated="$emit('field-updated', $event)"
        @field-deleted="$emit('field-deleted')"
        @update="$emit('update', $event)"
        @toggle-field-visibility="$emit('toggle-field-visibility', $event)"
      ></RowEditModalField>
    </li>
  </ul>
</template>

<script>
import RowEditModalField from '@baserow/modules/database/components/row/RowEditModalField'

export default {
  name: 'RowEditModalFieldsList',
  components: {
    RowEditModalField,
  },
  props: {
    primaryIsSortable: {
      type: Boolean,
      required: false,
      default: false,
    },
    fields: {
      type: Array,
      required: true,
    },
    sortable: {
      type: Boolean,
      required: true,
    },
    canModifyFields: {
      type: Boolean,
      required: false,
      default: true,
    },
    hidden: {
      type: Boolean,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  methods: {
    fieldIsSortable(field) {
      return this.sortable && (this.primaryIsSortable || !field.primary)
    },
  },
}
</script>
