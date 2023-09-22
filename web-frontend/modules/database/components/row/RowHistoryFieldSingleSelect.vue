<template>
  <div class="row-history-entry__field-content">
    <div v-if="entry.before[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--removed">
        {{ selectOptionValue(entry.before[fieldIdentifier]) }}
      </div>
    </div>
    <div v-if="entry.after[fieldIdentifier]">
      <div class="row-history-entry__diff row-history-entry__diff--added">
        {{ selectOptionValue(entry.after[fieldIdentifier]) }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowHistoryFieldSingleSelect',
  props: {
    entry: {
      type: Object,
      required: true,
    },
    fieldIdentifier: {
      type: String,
      required: true,
    },
  },
  methods: {
    selectOptionValue(id) {
      const value =
        this.entry.fields_metadata[this.fieldIdentifier].select_options[id]
          ?.value
      return value || id
    },
  },
}
</script>
