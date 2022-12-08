<template>
  <div>
    <div class="member-roles-tab__header">
      <h2>
        {{
          $t(`memberRolesTab.${translationPrefix}.title`, { name: scope.name })
        }}
      </h2>
      <a
        :class="{ 'button--loading': loading }"
        class="button button--ghost"
        @click="loading ? null : $refs.roleAssignmentModal.show()"
        >{{ $t(`memberRolesTab.${translationPrefix}.selectMembers`) }}</a
      >
    </div>
    <span
      v-if="$featureFlags.includes('rbacNoRole')"
      class="member-roles-tab__everyone_access_label"
    >
      {{ descriptionText }}
    </span>
    <MemberRolesShareToggle
      v-if="$featureFlags.includes('rbacNoRole')"
      :name="scope.name"
      :toggled.sync="isSharedWithEveryone"
    />
    <div v-if="loading" class="loading"></div>
    <MemberRolesMembersList
      v-else
      :role-assignments="roleAssignments"
      :scope-type="scopeType"
      :scope-id="scopeId"
      :group-id="group.id"
      @role-updated="
        (roleAssignment, newRole) =>
          $emit('role-updated', roleAssignment, newRole)
      "
    />
    <RoleAssignmentModal
      ref="roleAssignmentModal"
      :users="groupUsersNotInvited"
      :teams="teamsNotInvited"
      @invite-teams="(teams, role) => $emit('invite-teams', teams, role)"
      @invite-members="
        (members, role) => $emit('invite-members', members, role)
      "
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import MemberRolesMembersList from '@baserow_enterprise/components/member-roles/MemberRolesMembersList'
import MemberRolesShareToggle from '@baserow_enterprise/components/member-roles/MemberRolesShareToggle'
import RoleAssignmentModal from '@baserow_enterprise/components/member-roles/RoleAssignmentModal'

export default {
  name: 'MemberRolesTab',
  components: {
    RoleAssignmentModal,
    MemberRolesShareToggle,
    MemberRolesMembersList,
  },
  props: {
    group: {
      type: Object,
      required: true,
    },
    scope: {
      type: Object,
      required: true,
    },
    scopeType: {
      type: String,
      required: true,
    },
    roleAssignments: {
      type: Array,
      required: false,
      default: () => [],
    },
    teams: {
      type: Array,
      required: false,
      default: () => [],
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      isSharedWithEveryone: true,
    }
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
    scopeId() {
      return this.scope.id || null
    },
    translationPrefix() {
      switch (this.scopeType) {
        case 'database':
          return 'database'
        case 'database_table':
          return 'table'
        default:
          return 'database'
      }
    },
    descriptionText() {
      return this.isSharedWithEveryone
        ? this.$t(
            `memberRolesTab.${this.translationPrefix}.everyoneHasAccess`,
            {
              name: this.scope.name,
            }
          )
        : this.$t(`memberRolesTab.${this.translationPrefix}.onlyYouHaveAccess`)
    },
    userRoleAssignments() {
      return this.roleAssignments.filter(
        (roleAssignment) => roleAssignment.subject_type === 'auth.User'
      )
    },
    teamRoleAssignments() {
      return this.roleAssignments.filter(
        (roleAssignment) =>
          roleAssignment.subject_type === 'baserow_enterprise.Team'
      )
    },
    groupUsers() {
      return this.group.users || []
    },
    groupUsersNotInvited() {
      const userIds = this.userRoleAssignments.map(({ subject }) => subject.id)
      return this.groupUsers.filter(
        ({ user_id: userId }) =>
          !userIds.includes(userId) && userId !== this.userId
      )
    },
    teamsNotInvited() {
      const teamIds = this.teamRoleAssignments.map(({ subject }) => subject.id)
      return this.teams.filter(({ id }) => !teamIds.includes(id))
    },
  },
}
</script>
