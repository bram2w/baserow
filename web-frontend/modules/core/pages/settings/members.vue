<template>
  <div>
    <Tabs>
      <Tab :title="$t('membersSettings.membersTabTitle')">
        <MembersTable :group="group" @invite-submitted="refreshInvitesTable" />
      </Tab>
      <Tab :title="$t('membersSettings.invitesTabTitle')">
        <MembersInvitesTable
          ref="invitesTable"
          :group="group"
          @invite-submitted="refreshInvitesTable"
        />
      </Tab>
    </Tabs>
  </div>
</template>

<script>
import MembersTable from '@baserow/modules/core/components/settings/members/MembersTable'
import MembersInvitesTable from '@baserow/modules/core/components/settings/members/MembersInvitesTable'
export default {
  name: 'Members',
  components: { MembersInvitesTable, MembersTable },
  middleware: 'admin',
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  methods: {
    refreshInvitesTable() {
      this.$refs.invitesTable.refresh()
    },
  },
}
</script>
