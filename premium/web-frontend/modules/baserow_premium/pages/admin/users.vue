<template>
  <UsersAdminTable></UsersAdminTable>
</template>

<script>
import UsersAdminTable from '@baserow_premium/components/admin/users/UsersAdminTable'

export default {
  components: { UsersAdminTable },
  layout: 'app',
  middleware: 'staff',
}
</script>
