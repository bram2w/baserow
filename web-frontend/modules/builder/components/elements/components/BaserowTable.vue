<template>
  <div class="baserow-table-wrapper">
    <table class="baserow-table" :class="`baserow-table--${orientation}`">
      <template v-if="orientation === TABLE_ORIENTATION.HORIZONTAL">
        <thead>
          <tr class="baserow-table__row">
            <th
              v-for="field in fields"
              :key="field.__id__"
              class="baserow-table__header-cell"
            >
              <slot name="field-name" :field="field">{{ field.name }}</slot>
            </th>
          </tr>
        </thead>
        <tbody v-if="rows.length">
          <tr
            v-for="(row, index) in rows"
            :key="row.__id__"
            class="baserow-table__row"
          >
            <td
              v-for="field in fields"
              :key="field.id"
              class="baserow-table__cell"
            >
              <slot
                name="cell-content"
                :value="row[field.name]"
                :field="field"
                :row-index="index"
              >
                {{ value }}
              </slot>
            </td>
          </tr>
        </tbody>
      </template>
      <template v-else>
        <tbody v-if="rows.length">
          <template v-for="(row, rowIndex) in rows">
            <tr
              v-for="(field, fieldIndex) in fields"
              :key="`${row.__id__}_${field.id}`"
              class="baserow-table__row"
            >
              <th
                class="baserow-table__header-cell"
                :class="{
                  'baserow-table__separator': fieldIndex === fields.length - 1,
                }"
              >
                {{ field.name }}
              </th>
              <td
                class="baserow-table__cell"
                :class="{
                  'baserow-table__separator': fieldIndex === fields.length - 1,
                }"
              >
                <slot
                  name="cell-content"
                  :value="row[field.name]"
                  :field="field"
                  :row-index="rowIndex"
                >
                  {{ value }}
                </slot>
              </td>
            </tr>
          </template>
        </tbody>
      </template>
      <tbody v-if="!rows.length">
        <tr>
          <td class="baserow-table__empty-message" :colspan="fields.length">
            <slot name="empty-state"></slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { TABLE_ORIENTATION } from '@baserow/modules/builder/enums'

export default {
  name: 'BaserowTable',
  inject: ['mode'],
  props: {
    fields: {
      type: Array,
      required: true,
    },
    rows: {
      type: Array,
      required: true,
    },
    orientation: {
      type: String,
      default: TABLE_ORIENTATION.HORIZONTAL,
    },
  },
  data() {
    return {}
  },
  computed: {
    TABLE_ORIENTATION() {
      return TABLE_ORIENTATION
    },
  },
}
</script>
