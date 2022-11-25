<template>
  <ul class="list">
    <li
      v-for="roleAssignment in roleAssignmentsSorted"
      :key="roleAssignment.subject.id"
      class="list__item"
    >
      <!-- User subjects -->
      <div
        v-if="roleAssignment.subject_type === 'auth.User'"
        class="member-roles-members-list__subject-section"
      >
        <div class="member-roles-members-list__user-initials">
          {{ roleAssignment.subject.first_name | nameAbbreviation }}
        </div>
        <div
          v-tooltip="roleAssignment.subject.first_name"
          class="margin-left-1 member-roles-members-list__user-name"
        >
          {{ roleAssignment.subject.first_name }}
        </div>
      </div>

      <!-- Team subjects -->
      <div v-else class="member-roles-members-list__subject-section">
        <div class="member-roles-members-list__team-initials">
          {{ roleAssignment.subject.name | nameAbbreviation }}
        </div>
        <div
          v-tooltip="roleAssignment.subject.name"
          class="margin-left-1 member-roles-members-list__team-name"
        >
          {{ roleAssignment.subject.name }}
          <div class="member-roles-members-list__team-member-count">
            {{
              $t('memberRolesMembersList.teamMembersCount', {
                count: roleAssignment.subject.subject_count,
              })
            }}
          </div>
        </div>
      </div>
      <RoleSelector
        :disabled="
          roleAssignment.subject.id === userId &&
          roleAssignment.subject_type === 'auth.User'
        "
        :roles="roles"
        :value="getRole(roleAssignment)"
        :allow-removing-role="true"
        @delete="$emit('role-updated', roleAssignment, null)"
        @input="({ uid }) => $emit('role-updated', roleAssignment, uid)"
      />
    </li>
  </ul>
</template>

<script>
import { mapGetters } from 'vuex'
import RoleSelector from '@baserow_enterprise/components/member-roles/RoleSelector'

export default {
  name: 'MemberRolesMembersList',
  components: { RoleSelector },
  props: {
    roleAssignments: {
      type: Array,
      required: false,
      default: () => [],
    },
    scopeId: {
      type: Number,
      required: true,
    },
    scopeType: {
      type: String,
      required: true,
    },
    groupId: {
      type: Number,
      required: true,
    },
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
    group() {
      return this.$store.getters['group/get'](this.groupId)
    },
    roles() {
      return this.group ? this.group._.roles : []
    },
    roleAssignmentsSorted() {
      return [...this.roleAssignments].sort((a, b) =>
        a.subject_type > b.subject_type ? 1 : -1
      )
    },
  },
  methods: {
    getRole(roleAssignment) {
      return this.roles.find((role) => role.uid === roleAssignment.role)
    },
  },
}
</script>
