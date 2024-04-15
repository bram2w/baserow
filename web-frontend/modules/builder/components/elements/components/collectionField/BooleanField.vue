<template>
  <ABCheckbox :value="value" :read-only="true" />
</template>

<script>
import ABCheckbox from '@baserow/modules/builder/components/elements/baseComponents/ABCheckbox'

export default {
  name: 'BooleanField',
  components: { ABCheckbox },
  props: {
    value: {
      type: Boolean,
      required: true,
      default: false,
    },
  },
}
</script>
