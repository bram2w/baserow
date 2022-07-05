<template>
  <Context ref="context">
    <ViewDecoratorList
      :database="database"
      :view="view"
      @select="$emit('select', $event)"
    />
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import ViewDecoratorList from '@baserow/modules/database/components/view/ViewDecoratorList'

export default {
  name: 'AddViewDecoratorContext',
  components: {
    ViewDecoratorList,
  },
  mixins: [context],
  props: {
    database: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
  },
}
</script>
