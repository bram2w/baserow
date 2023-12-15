<template>
  <component
    :is="formulaComponent"
    :data-providers-allowed="dataProvidersAllowed || []"
    v-bind="$attrs"
    v-on="$listeners"
  />
</template>

<script>
export default {
  name: 'InjectedFormulaInputGroup',
  inject: ['formulaComponent', 'dataProvidersAllowed'],
}
</script>
