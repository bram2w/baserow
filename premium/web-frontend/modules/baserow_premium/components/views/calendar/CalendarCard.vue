<template>
  <div class="calendar-card" @click="$emit('edit-row', row)">
    {{ cardContent }}
  </div>
</template>

<script>
import {
  sortFieldsByOrderAndIdFunction,
  filterVisibleFieldsFunction,
} from '@baserow/modules/database/utils/view'

export default {
  name: 'CalendarCard',
  props: {
    row: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  computed: {
    visibleCardFields() {
      const fieldOptions =
        this.$store.getters[
          this.storePrefix + 'view/calendar/getAllFieldOptions'
        ]
      return this.fields
        .filter(filterVisibleFieldsFunction(fieldOptions))
        .sort(sortFieldsByOrderAndIdFunction(fieldOptions))
    },
    cardContent() {
      return this.visibleCardFields
        .map((f) => {
          const fieldType = this.$registry.get('field', f.type)
          const cellValue = this.row[`field_${f.id}`]
          return fieldType.toHumanReadableString(f, cellValue)
        })
        .join(' - ')
    },
  },
}
</script>
