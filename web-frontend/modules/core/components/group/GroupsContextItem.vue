<template>
  <li
    class="select__item"
    :class="{
      active: group._.selected,
      'select__item--loading': group._.loading,
      'select__item--no-options': group.permissions !== 'ADMIN',
    }"
  >
    <a class="select__item-link" @click="selectGroup(group)">
      <div class="select__item-name">
        <Editable
          ref="rename"
          :value="group.name"
          @change="renameGroup(group, $event)"
        ></Editable>
      </div>
    </a>
    <a
      v-if="group.permissions === 'ADMIN'"
      ref="contextLink"
      class="select__item-options"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="fas fa-ellipsis-v"></i>
    </a>
    <GroupContext
      ref="context"
      :group="group"
      @rename="enableRename()"
    ></GroupContext>
  </li>
</template>

<script>
import GroupContext from '@baserow/modules/core/components/group/GroupContext'
import editGroup from '@baserow/modules/core/mixins/editGroup'

export default {
  name: 'GroupsContextItem',
  components: { GroupContext },
  mixins: [editGroup],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
}
</script>
