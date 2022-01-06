<template>
  <div
    class="card"
    :class="{ 'card--loading': loading }"
    @mousedown="$emit('mousedown', $event)"
    @mousemove="$emit('mousemove', $event)"
    @mouseenter="$emit('mouseenter', $event)"
  >
    <div v-for="field in fields" :key="field.id" class="card__field">
      <div class="card__field-name">{{ field.name }}</div>
      <div class="card__field-value">
        <component
          :is="getCardComponent(field)"
          v-if="!loading"
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
      required: false,
      default: () => {},
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  methods: {
    getCardComponent(field) {
      return this.$registry.get('field', field.type).getCardComponent()
    },
  },
}
</script>
