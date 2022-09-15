<template>
  <div class="control">
    <div class="simple-grid__head">
      <div v-for="field in fields" :key="field.id" class="simple-grid__field">
        <i
          class="fas simple-grid__field-icon"
          :class="'fa-' + fieldTypes[field.type].iconClass"
        ></i>
        {{ field.name }}
      </div>
    </div>
    <div class="simple-grid__body">
      <div v-for="row in rows" :key="row.id" class="simple-grid__row">
        <div v-for="field in fields" :key="field.id" class="simple-grid__cell">
          <SimpleGridField :field="field" :row="row" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SimpleGridField from './SimpleGridField'
export default {
  name: 'SimpleGrid',
  components: { SimpleGridField },
  props: {
    rows: {
      type: Array,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  computed: {
    fieldTypes() {
      return this.$registry.getAll('field')
    },
  },
}
</script>
