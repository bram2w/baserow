<template>
  <UserAdminTable></UserAdminTable>
</template>

<script>
import UserAdminTable from '@baserow_premium/components/admin/user/UserAdminTable'

export default {
  components: { UserAdminTable },
  layout: 'app',
  middleware: 'staff',
}
</script>
