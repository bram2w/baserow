<template>
  <MembersInvitesTable :workspace="workspace" />
</template>

<script>
import MembersInvitesTable from '@baserow/modules/core/components/settings/members/MembersInvitesTable'

export default {
  name: 'Invites',
  components: { MembersInvitesTable },
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
}
</script>
