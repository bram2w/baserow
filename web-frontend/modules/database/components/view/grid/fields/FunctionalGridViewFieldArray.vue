<template functional>
  <!--  Vue 2 does not support nested importing of components other than this way -->
  <component
    :is="$options.components.FunctionalFormulaArrayItems"
    class="grid-view__cell grid-view-array-field"
    :class="[data.staticClass, data.class]"
    :field="props.field"
    :value="props.value"
    :selected="props.selected"
    v-on="listeners"
  >
    <slot></slot>
  </component>
</template>

<script>
import FunctionalFormulaArrayItems from '@baserow/modules/database/components/formula/array/FunctionalFormulaArrayItems'

export default {
  name: 'FunctionalGridViewFieldArray',
  components: { FunctionalFormulaArrayItems },
}
</script>
