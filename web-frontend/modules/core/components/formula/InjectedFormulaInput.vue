<template>
  <component
    :is="formulaComponent"
    :data-providers-allowed="dataProvidersAllowed || []"
    v-bind="$attrs"
    v-on="$listeners"
  >
    <template #after-input>
      <slot name="after-input"></slot>
    </template>
  </component>
</template>

<script>
export default {
  name: 'InjectedFormulaInput',
  inject: ['formulaComponent', 'dataProvidersAllowed'],
}
</script>
