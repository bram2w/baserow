<template>
  <Modal>
    <Tabs>
      <Tab :title="$t('roleAssignmentModal.membersTab')">
        <SelectMembersList
          class="margin-top-2"
          :users="users"
          show-role-selector
          @invite="(...params) => onInvite('invite-members', ...params)"
        />
      </Tab>
      <Tab :title="$t('roleAssignmentModal.teamsTab')">
        <SelectTeamsList
          class="margin-top-2"
          :teams="teams"
          show-role-selector
          @invite="(...params) => onInvite('invite-teams', ...params)"
        />
      </Tab>
    </Tabs>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'
import SelectMembersList from '@baserow_enterprise/components/rbac/SelectMembersList'
import SelectTeamsList from '@baserow_enterprise/components/rbac/SelectTeamsList'

export default {
  name: 'RoleAssignmentModal',
  components: { SelectTeamsList, SelectMembersList },
  mixins: [Modal],
  props: {
    users: {
      type: Array,
      required: false,
      default: () => [],
    },
    teams: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  methods: {
    onInvite(eventName, ...params) {
      this.$emit(eventName, ...params)
      this.hide()
    },
  },
}
</script>
