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
        <template v-if="getFieldName(field) && getEntryComponent(field)">
          <div :key="field" class="row-history-entry__field">
            {{ getFieldName(field) }}
          </div>
          <component
            :is="getEntryComponent(field)"
            :key="field + 'content'"
            :entry="entry"
            :field-identifier="field"
          ></component>
        </template>
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
    fields: {
      type: Array,
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
    getFieldName(fieldIdentifier) {
      const id = this.entry.fields_metadata[fieldIdentifier].id
      const field = this.fields.find((f) => f.id === id)
      if (field) {
        return field.name
      }
      return null
    },
    getEntryComponent(fieldIdentifier) {
      const type = this.entry.fields_metadata[fieldIdentifier].type
      const fieldType = this.$registry.get('field', type)
      if (fieldType) {
        return fieldType.getRowHistoryEntryComponent()
      }
      return null
    },
  },
}
</script>
