<template>
  <div class="row-history-entry__field-content">
    <div
      class="row-history-entry__diff"
      :class="
        action === 'deleted'
          ? 'row-history-entry__diff--removed'
          : 'row-history-entry__diff--added'
      "
    >
      {{ text }}
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
  computed: {
    action() {
      if (
        !this.entry.before[this.fieldIdentifier] &&
        this.entry.after[this.fieldIdentifier]
      ) {
        return 'set'
      } else if (
        this.entry.before[this.fieldIdentifier] &&
        this.entry.after[this.fieldIdentifier]
      ) {
        return 'updated'
      } else {
        return 'deleted'
      }
    },
    text() {
      if (this.action === 'set') {
        return this.$t('rowHistoryFieldPassword.passwordSet')
      } else if (this.action === 'updated') {
        return this.$t('rowHistoryFieldPassword.passwordUpdated')
      } else {
        return this.$t('rowHistoryFieldPassword.passwordDeleted')
      }
    },
  },
}
</script>
