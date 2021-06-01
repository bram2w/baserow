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
        <EditableViewName ref="rename" :view="view"></EditableViewName>
      </div>
    </a>
    <template v-if="!readOnly">
      <a
        ref="contextLink"
        class="select__item-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        @mousedown.stop
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <ViewContext
        ref="context"
        :table="table"
        :view="view"
        @enable-rename="enableRename"
      ></ViewContext>
    </template>
  </li>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import ViewContext from '@baserow/modules/database/components/view/ViewContext'
import EditableViewName from '@baserow/modules/database/components/view/EditableViewName'

export default {
  name: 'ViewsContextItem',
  components: { EditableViewName, ViewContext },
  mixins: [context],
  props: {
    view: {
      type: Object,
      required: true,
    },
    table: {
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
    enableRename() {
      this.$refs.rename.edit()
    },
  },
}
</script>
