<template>
  <InjectedFormulaInputGroup v-model="fieldValue" v-bind="$attrs" />
</template>

<script>
import InjectedFormulaInputGroup from '@baserow/modules/core/components/formula/InjectedFormulaInputGroup'

export default {
  name: 'FieldMapping',
  components: { InjectedFormulaInputGroup },
  props: {
    field: {
      type: Object,
      required: true,
    },
    value: {
      type: String,
      required: false,
      default: () => '',
    },
  },
  computed: {
    fieldValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('change', value)
      },
    },
  },
}
</script>
