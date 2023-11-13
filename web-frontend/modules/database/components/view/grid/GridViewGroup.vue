<template functional>
  <div class="grid-view__group" :style="[data.staticStyle, data.style]">
    <div
      class="grid-view__group-cell"
      :set="
        (field = $options.methods.getField(
          props.allFieldsInTable,
          props.groupBy
        ))
      "
    >
      <div class="grid-view__group-name">
        {{ field.name }}
      </div>
      <div class="grid-view__group-value">
        <component
          :is="$options.methods.getCardComponent(field, parent)"
          :field="field"
          :value="props.value"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GridViewGroup',
  props: {
    groupBy: {
      type: Object,
      required: true,
    },
    allFieldsInTable: {
      type: Array,
      required: true,
    },
    value: {
      validator: () => true,
      required: true,
    },
  },
  methods: {
    getField(allFieldsInTable, groupBy) {
      const field = allFieldsInTable.find((f) => f.id === groupBy.field)
      return field
    },
    getCardComponent(field, parent) {
      const fieldType = parent.$registry.get('field', field.type)
      return fieldType.getGroupByComponent(field)
    },
  },
}
</script>
