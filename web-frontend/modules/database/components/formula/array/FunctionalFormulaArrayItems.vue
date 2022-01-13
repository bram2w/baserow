<template functional>
  <div :class="[data.staticClass, data.class]">
    <component
      :is="$options.methods.getComponent(props.field, parent.$registry)"
      v-for="(item, index) in props.value || []"
      :key="index"
      :field="props.field"
      :value="item && item.value"
    ></component>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaArrayItems',
  methods: {
    getComponent(field, $registry) {
      const formulaType = $registry.get(
        'formula_type',
        field.array_formula_type
      )
      return formulaType.getFunctionalGridViewFieldArrayComponent()
    },
  },
}
</script>
