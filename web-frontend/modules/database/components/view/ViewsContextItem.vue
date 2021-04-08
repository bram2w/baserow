<template>
  <li
    class="select__item"
    :class="{
      active: view._.selected,
      'select__item--loading': view._.loading,
      'select__item--no-options': readOnly,
    }"
  >
    <a class="select__item-link" @click="$emit('selected', view)">
      <div class="select__item-name">
        <i
          class="select__item-icon fas fa-fw color-primary"
          :class="'fa-' + view._.type.iconClass"
        ></i>
        <Editable
          ref="rename"
          :value="view.name"
          @change="renameView(view, $event)"
        ></Editable>
      </div>
    </a>
    <template v-if="!readOnly">
      <a
        ref="contextLink"
        class="select__item-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <Context ref="context">
        <ul class="context__menu">
          <li>
            <a @click="enableRename()">
              <i class="context__menu-icon fas fa-fw fa-pen"></i>
              Rename view
            </a>
          </li>
          <li>
            <a @click="deleteView()">
              <i class="context__menu-icon fas fa-fw fa-trash"></i>
              Delete view
            </a>
          </li>
        </ul>
      </Context>
      <DeleteViewModal ref="deleteViewModal" :view="view" />
    </template>
  </li>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import DeleteViewModal from './DeleteViewModal'

export default {
  name: 'ViewsContextItem',
  components: { DeleteViewModal },
  mixins: [context],
  props: {
    view: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: true,
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
        notifyIf(error, 'view')
      }

      this.setLoading(view, false)
    },
    deleteView() {
      this.$refs.context.hide()
      this.$refs.deleteViewModal.show()
    },
  },
}
</script>
