<template>
  <div class="row-history-entry__field-content">
    <div v-if="removedItems">
      <div
        v-for="item in removedItems"
        :key="item"
        class="row-history-entry__diff row-history-entry__diff--removed"
      >
        {{ selectOptionValue(item) }}
      </div>
    </div>
    <div v-if="addedItems">
      <div
        v-for="item in addedItems"
        :key="item"
        class="row-history-entry__diff row-history-entry__diff--added"
      >
        {{ selectOptionValue(item) }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowHistoryFieldMultipleSelect',
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
  computed: {
    removedItems() {
      return this.entry.before[this.fieldIdentifier].filter((before) => {
        return (
          this.entry.after[this.fieldIdentifier].findIndex(
            (item) => item === before
          ) === -1
        )
      })
    },
    addedItems() {
      return this.entry.after[this.fieldIdentifier].filter((after) => {
        return (
          this.entry.before[this.fieldIdentifier].findIndex(
            (item) => item === after
          ) === -1
        )
      })
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
