<template>
  <ExpandOnOverflowList
    ref="expandOnOverflow"
    :row="row"
    :column="column"
    :name-key="nameKey"
  >
    <template #icon="{ record }">
      <i
        v-if="record.permissions === 'ADMIN'"
        v-tooltip="$t('premium.user.isGroupAdmin')"
        class="user-admin-group__icon fas fa-users-cog"
      ></i>
    </template>
  </ExpandOnOverflowList>
</template>
<script>
import ExpandOnOverflowList from '@baserow/modules/core/components/crudTable/ExpandOnOverflowList'

/**
 * Displays a list of a groups with a modal displaying any groups that do not fit.
 */
export default {
  name: 'UserGroupsField',
  components: {
    ExpandOnOverflowList,
  },
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      nameKey: 'name',
    }
  },
}
</script>
