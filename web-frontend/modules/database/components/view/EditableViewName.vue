<template>
  <Editable
    ref="rename"
    :value="view.name"
    @change="renameView(view, $event)"
  ></Editable>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'EditableViewName',
  components: {},
  props: {
    view: {
      type: Object,
      required: true,
    },
  },
  methods: {
    setLoading(view, value) {
      this.$store.dispatch('view/setItemLoading', { view, value })
    },
    edit() {
      this.$refs.rename.edit()
    },
    async renameView(view, event) {
      this.setLoading(view, true)

      try {
        await this.$store.dispatch('view/update', {
          view,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.setLoading(view, false)
    },
  },
}
</script>
