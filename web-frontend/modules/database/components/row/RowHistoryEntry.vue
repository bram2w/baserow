<template>
  <div class="row-history-entry">
    <div class="row-history-entry__header">
      <span class="row_history-entry__initials">{{ initials }}</span>
      <span class="row-history-entry__name">{{ name }}</span>
      <span class="row-history-entry__timestamp" :title="timestampTooltip">{{
        formattedTimestamp
      }}</span>
    </div>
    <div class="row-history-entry__content">
      <template v-for="field in entryFields">
        <div :key="field" class="row-history-entry__field">{{ field }}</div>
        <div :key="field + 'content'" class="row-history-entry__field-content">
          <div v-if="entry.before[field]">
            <div
              class="row-history-entry__diff row-history-entry__diff--removed"
            >
              {{ entry.before[field] }}
            </div>
          </div>
          <div v-if="entry.after[field]">
            <div class="row-history-entry__diff row-history-entry__diff--added">
              {{ entry.after[field] }}
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'RowHistoryEntry',
  props: {
    entry: {
      type: Object,
      required: true,
    },
  },
  computed: {
    name() {
      return this.entry.user.name
    },
    initials() {
      return this.name.slice(0, 1).toUpperCase()
    },
    timestampTooltip() {
      return this.getLocalizedMoment(this.entry.timestamp).format('L LT')
    },
    formattedTimestamp() {
      return this.getLocalizedMoment(this.entry.timestamp).format('LT')
    },
    entryFields() {
      return new Set(
        Object.keys(this.entry.before).concat(Object.keys(this.entry.after))
      )
    },
  },
  methods: {
    getLocalizedMoment(timestamp) {
      return moment.utc(timestamp).tz(moment.tz.guess())
    },
  },
}
</script>
