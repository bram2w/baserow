<template functional>
  <component
    :is="$options.methods.getComponent(props.field)"
    v-if="$options.methods.getComponent(props.field)"
    :field="props.field"
    :value="props.value"
  ></component>
  <div v-else class="card-text">Unknown Field Type</div>
</template>

<script>
import RowCardFieldDate from '@baserow/modules/database/components/card/RowCardFieldDate'
import RowCardFieldBoolean from '@baserow/modules/database/components/card/RowCardFieldBoolean'
import RowCardFieldNumber from '@baserow/modules/database/components/card/RowCardFieldNumber'
import RowCardFieldText from '@baserow/modules/database/components/card/RowCardFieldText'

export default {
  height: 0, // @TODO make this work for the formula
  name: 'RowCardFieldFormula',
  components: {
    RowCardFieldDate,
    RowCardFieldBoolean,
    RowCardFieldNumber,
    RowCardFieldText,
  },
  methods: {
    getComponent(field) {
      return {
        date: RowCardFieldDate,
        text: RowCardFieldText,
        boolean: RowCardFieldBoolean,
        number: RowCardFieldNumber,
        invalid: RowCardFieldText,
        char: RowCardFieldText,
        date_interval: RowCardFieldText,
      }[field.formula_type]
    },
  },
}
</script>
