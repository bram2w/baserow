<template functional>
  <div
    class="grid-view__group"
    :style="{ width: props.width + 'px' }"
    :class="{
      'grid-view__group--end': props.end,
    }"
  >
    <div
      v-if="props.start"
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
          :value="props.row['field_' + field.id]"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GridViewRowGroup',
  props: {
    width: {
      type: Number,
      required: true,
    },
    start: {
      type: Boolean,
      required: true,
    },
    end: {
      type: Boolean,
      required: true,
    },
    groupBy: {
      type: Object,
      required: true,
    },
    allFieldsInTable: {
      type: Array,
      required: true,
    },
    row: {
      type: Object,
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
