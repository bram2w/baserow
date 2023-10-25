<template>
  <div class="row-history-entry__field-content">
    <div v-if="entry.before[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--removed">
        {{ entry.before[fieldIdentifier] }}
      </div>
    </div>
    <div v-if="entry.after[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--added">
        {{ entry.after[fieldIdentifier] }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowHistoryFieldText',
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
}
</script>
