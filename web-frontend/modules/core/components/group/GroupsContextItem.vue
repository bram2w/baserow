<template>
  <li
    class="select-item"
    :class="{
      active: group._.selected,
      'select-item-loading': group._.loading,
    }"
  >
    <div class="loading-overlay"></div>
    <a class="select-item-link" @click="selectGroup(group)">
      <Editable
        ref="rename"
        :value="group.name"
        @change="renameGroup(group, $event)"
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
            Rename group
          </a>
        </li>
        <li>
          <a @click="deleteGroup(group)">
            <i class="context-menu-icon fas fa-fw fa-trash"></i>
            Delete group
          </a>
        </li>
      </ul>
    </Context>
  </li>
</template>

<script>
import editGroup from '@baserow/modules/core/mixins/editGroup'

export default {
  name: 'GroupsContextItem',
  mixins: [editGroup],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
}
</script>
