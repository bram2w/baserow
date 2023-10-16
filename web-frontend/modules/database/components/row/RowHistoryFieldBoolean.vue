<template>
  <div class="row-history-entry__field-content">
    <div v-if="entry.before[fieldIdentifier]">
      <div
        class="row-history-entry__diff row-history-entry__diff--removed row-history-field-boolean__diff"
      >
        <i class="iconoir-check"></i>
      </div>
    </div>
    <div v-if="entry.after[fieldIdentifier]">
      <div
        class="row-history-entry__diff row-history-entry__diff--added row-history-field-boolean__diff"
      >
        <i class="iconoir-check"></i>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowHistoryFieldBoolean',
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
