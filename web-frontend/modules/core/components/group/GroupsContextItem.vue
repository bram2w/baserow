<template>
  <li
    class="select__item"
    :class="{
      active: group._.selected,
      'select__item--loading': group._.loading,
    }"
  >
    <a class="select__item-link" @click="selectGroup(group)">
      <Editable
        ref="rename"
        :value="group.name"
        @change="renameGroup(group, $event)"
      ></Editable>
    </a>
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
            Rename group
          </a>
        </li>
        <li>
          <a @click="deleteGroup(group)">
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
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
