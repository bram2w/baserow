<template>
  <div class="row-history-entry__field-content">
    <div v-if="entry.before[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--removed">
        {{ formattedDate(entry.before[fieldIdentifier]) }}
      </div>
    </div>
    <div v-if="entry.after[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--added">
        {{ formattedDate(entry.after[fieldIdentifier]) }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowHistoryFieldDate',
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
    formattedDate(value) {
      const metadata = this.entry.fields_metadata[this.fieldIdentifier]
      const type = this.entry.fields_metadata[this.fieldIdentifier].type
      const fieldType = this.$registry.get('field', type)
      return fieldType.toHumanReadableString(metadata, value)
    },
  },
}
</script>
