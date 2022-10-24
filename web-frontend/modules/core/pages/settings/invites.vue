<template>
  <MembersInvitesTable :group="group" />
</template>

<script>
import MembersInvitesTable from '@baserow/modules/core/components/settings/members/MembersInvitesTable'

export default {
  name: 'Invites',
  components: { MembersInvitesTable },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
}
</script>
