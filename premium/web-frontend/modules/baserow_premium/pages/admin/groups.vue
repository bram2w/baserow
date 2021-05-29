<template>
  <GroupsAdminTable></GroupsAdminTable>
</template>

<script>
import GroupsAdminTable from '@baserow_premium/components/admin/groups/GroupsAdminTable'

export default {
  components: { GroupsAdminTable },
  layout: 'app',
  middleware: 'staff',
}
</script>
