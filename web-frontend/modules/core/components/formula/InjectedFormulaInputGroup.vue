<template>
  <component
    :is="formulaComponent"
    :data-providers-allowed="dataProvidersAllowed || []"
    v-bind="$attrs"
    class="margin-bottom-2"
    v-on="$listeners"
  />
</template>

<script>
export default {
  name: 'InjectedFormulaInputGroup',
  inject: ['formulaComponent', 'dataProvidersAllowed'],
}
</script>
