<script>
import UserWorkspacesField from '@baserow_premium/components/admin/users/fields/UserWorkspacesField'

export default {
  name: 'WorkspaceUsersField',
  extends: UserWorkspacesField,
  data() {
    return {
      nameKey: 'email',
    }
  },
}
</script>
