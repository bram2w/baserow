<script>
import HiddenGroupsContext from '@baserow_premium/components/admin/users/contexts/HiddenGroupsContext'

export default {
  name: 'HiddenUsersContext',
  extends: HiddenGroupsContext,
  data() {
    return {
      nameKey: 'email',
    }
  },
}
</script>
