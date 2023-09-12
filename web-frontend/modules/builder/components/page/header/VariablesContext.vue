<template>
  <Context
    class="variables-context"
    :overflow-scroll="true"
    :max-height-if-outside-viewport="true"
  >
    Variables
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'VariablesContext',
  mixins: [context],
  data() {
    return {}
  },
}
</script>
