<template>
  <div>
    <UserPermissionsModal
      ref="userPermissionsModal"
      :database="database"
      :table="table"
      :fields="fields"
      @hidden="$router.push({ name: 'database-table', params: $route.params })"
    />
  </div>
</template>

<script>
import UserPermissionsModal from '@baserow/modules/database/components/userPermissions/UserPermissionsModal'

export default {
  name: 'UserPermissionsPage',
  components: { 
    UserPermissionsModal 
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.$refs.userPermissionsModal.show()
    })
  },
}
</script>