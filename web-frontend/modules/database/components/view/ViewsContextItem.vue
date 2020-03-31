<template>
  <li
    class="select-item"
    :class="{
      active: view._.selected,
      'select-item-loading': view._.loading,
    }"
  >
    <div class="loading-overlay"></div>
    <a class="select-item-link" @click="selectView(view)">
      <i
        class="select-item-icon fas fa-fw color-primary"
        :class="'fa-' + view._.type.iconClass"
      ></i>
      <Editable
        ref="rename"
        :value="view.name"
        @change="renameView(view, $event)"
      ></Editable>
    </a>
    <a
      ref="contextLink"
      class="select-item-options"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
    >
      <i class="fas fa-ellipsis-v"></i>
    </a>
    <Context ref="context">
      <ul class="context-menu">
        <li>
          <a @click="enableRename()">
            <i class="context-menu-icon fas fa-fw fa-pen"></i>
            Rename view
          </a>
        </li>
        <li>
          <a @click="deleteView(view)">
            <i class="context-menu-icon fas fa-fw fa-trash"></i>
            Delete view
          </a>
        </li>
      </ul>
    </Context>
  </li>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'ViewsContextItem',
  mixins: [context],
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
    enableRename() {
      this.$refs.context.hide()
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
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'view')
      }

      this.setLoading(view, false)
    },
    async deleteView(view) {
      this.$refs.context.hide()
      this.setLoading(view, true)

      try {
        await this.$store.dispatch('view/delete', view)
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.setLoading(view, false)
    },
    selectView(view) {
      this.setLoading(view, true)

      this.$nuxt.$router.push(
        {
          name: 'database-table',
          params: {
            viewId: view.id,
          },
        },
        () => {
          this.setLoading(view, false)
          this.$emit('selected')
        },
        () => {
          this.setLoading(view, false)
        }
      )
    },
  },
}
</script>
