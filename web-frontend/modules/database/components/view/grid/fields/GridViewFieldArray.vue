<template>
  <FunctionalGridViewFieldArray
    :field="field"
    :value="value"
    :selected="selected"
    v-on="$listeners"
  ></FunctionalGridViewFieldArray>
</template>

<script>
import FunctionalGridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray'
import gridField from '@baserow/modules/database/mixins/gridField'

export default {
  name: 'GridViewFieldArray',
  components: { FunctionalGridViewFieldArray },
  mixins: [gridField],
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
