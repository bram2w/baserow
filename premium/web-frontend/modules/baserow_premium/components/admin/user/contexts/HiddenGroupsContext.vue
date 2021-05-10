<template>
  <Context>
    <ul class="context__menu">
      <li
        v-for="group in hiddenGroups"
        :key="'hidden-admin-row-group' + group.id"
        class="user-admin-group__dropdown-item"
      >
        {{ group.name }}
        <i
          v-if="group.permissions == 'ADMIN'"
          v-tooltip="'is group admin'"
          class="user-admin-group__icon fas fa-users-cog"
        ></i>
      </li>
    </ul>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'HiddenGroupsContext',
  mixins: [context],
  props: {
    hiddenGroups: {
      required: true,
      type: Array,
    },
  },
}
</script>
