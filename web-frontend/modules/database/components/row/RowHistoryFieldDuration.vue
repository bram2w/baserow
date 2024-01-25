<template>
  <div class="row-history-entry__field-content">
    <div v-if="entry.before[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--removed">
        {{ formattedDuration(entry.before[fieldIdentifier]) }}
      </div>
    </div>
    <div v-if="entry.after[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--added">
        {{ formattedDuration(entry.after[fieldIdentifier]) }}
      </div>
    </div>
  </div>
</template>

<script>
import { DurationFieldType } from '@baserow/modules/database/fieldTypes'

export default {
  name: 'RowHistoryFieldNumber',
  props: {
    entry: {
      type: Object,
      required: true,
    },
    fieldIdentifier: {
      type: String,
      required: true,
    },
    field: {
      type: Object,
      required: false,
      default: null,
    },
  },
  methods: {
    formattedDuration(value) {
      const metadata = this.entry.fields_metadata[this.fieldIdentifier]
      const durationFieldType = this.$registry.get(
        'field',
        DurationFieldType.getType()
      )
      return durationFieldType.formatValue(metadata, value)
    },
  },
}
</script>
