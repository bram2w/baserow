<template>
  <div class="row-history-entry__field-content">
    <div v-if="removedItems">
      <div
        v-for="item in removedItems"
        :key="item.id"
        class="row-history-entry__diff row-history-entry__diff--removed"
      >
        {{ item.visible_name }}
      </div>
    </div>
    <div v-if="addedItems">
      <div
        v-for="item in addedItems"
        :key="item.id"
        class="row-history-entry__diff row-history-entry__diff--added"
      >
        {{ item.visible_name }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowHistoryFieldFile',
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
            (item) => item.id === before.id
          ) === -1
        )
      })
    },
    addedItems() {
      return this.entry.after[this.fieldIdentifier].filter((after) => {
        return (
          this.entry.before[this.fieldIdentifier].findIndex(
            (item) => item.id === after.id
          ) === -1
        )
      })
    },
  },
}
</script>
