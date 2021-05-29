<template>
  <Context>
    <ul class="context__menu">
      <li
        v-for="group in hiddenValues"
        :key="'hidden-admin-row-group' + group.id"
        class="user-admin-group__dropdown-item"
      >
        {{ group[nameKey] }}
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
    hiddenValues: {
      required: true,
      type: Array,
    },
  },
  data() {
    return {
      nameKey: 'name',
    }
  },
}
</script>
