<template>
  <FunctionalGridViewFieldArray
    :field="field"
    :value="value"
  ></FunctionalGridViewFieldArray>
</template>

<script>
import FunctionalGridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray'
import baseField from '@baserow/modules/database/mixins/baseField'

export default {
  name: 'GridViewFieldArray',
  components: { FunctionalGridViewFieldArray },
  mixins: [baseField],
}
</script>
