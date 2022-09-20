<template functional>
  <div class="card-array__wrapper">
    <component
      :is="$options.components.FunctionalFormulaArrayItems"
      class="card-array"
      :class="data.staticClass || ''"
      :field="props.field"
      :value="props.value"
      :selected="true"
    ></component>
  </div>
</template>

<script>
import FunctionalFormulaArrayItems from '@baserow/modules/database/components/formula/array/FunctionalFormulaArrayItems'

export default {
  height: 22,
  name: 'RowCardFieldArray',
  components: { FunctionalFormulaArrayItems },
}
</script>
