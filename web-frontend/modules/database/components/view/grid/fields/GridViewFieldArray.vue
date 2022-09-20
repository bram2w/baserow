<template>
  <FunctionalGridViewFieldArray
    :field="field"
    :value="value"
    :selected="selected"
  ></FunctionalGridViewFieldArray>
</template>

<script>
import FunctionalGridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray'
import baseField from '@baserow/modules/database/mixins/baseField'

export default {
  name: 'GridViewFieldArray',
  components: { FunctionalGridViewFieldArray },
  mixins: [baseField],
  props: {
    selected: {
      type: Boolean,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
}
</script>
