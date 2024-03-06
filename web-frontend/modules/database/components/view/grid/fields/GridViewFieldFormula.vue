<template functional>
  <component
    :is="$options.methods.getComponent(props.field, parent.$registry)"
    v-bind="data.attrs"
    :read-only="true"
    class="active"
    v-on="listeners"
  ></component>
</template>

<script>
export default {
  name: 'GridViewFieldFormula',
  methods: {
    getComponent(field, registry) {
      return registry
        .get('formula_type', field.formula_type)
        .getGridViewFieldComponent(field)
    },
  },
}
</script>
