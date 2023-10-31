<template>
  <table class="baserow-table">
    <thead>
      <tr class="baserow-table__header-row">
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
      <tr v-for="row in rows" :key="row.__id__" class="baserow-table__row">
        <td v-for="field in fields" :key="field.id" class="baserow-table__cell">
          <slot name="cell-content" :value="row[field.name]" :field="field">
            {{ value }}
          </slot>
        </td>
      </tr>
    </tbody>
    <tbody v-else>
      <tr>
        <td class="baserow-table__empty-message" :colspan="fields.length">
          <slot name="empty-state"></slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: 'BaserowTable',
  props: {
    fields: {
      type: Array,
      required: true,
    },
    rows: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {}
  },
  computed: {},
  watch: {},
  methods: {},
}
</script>
