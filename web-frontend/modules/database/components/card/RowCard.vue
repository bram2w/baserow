<template>
  <div class="card" v-on="$listeners">
    <div v-for="field in fields" :key="field.id" class="card__field">
      <div class="card__field-name">{{ field.name }}</div>
      <div class="card__field-value">
        <component
          :is="getCardComponent(field)"
          :field="field"
          :value="row['field_' + field.id]"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RowCard',
  props: {
    fields: {
      type: Array,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getCardComponent(field) {
      return this.$registry.get('field', field.type).getCardComponent()
    },
  },
}
</script>
