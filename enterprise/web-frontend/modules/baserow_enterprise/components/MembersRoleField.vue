<template>
  <div>
    <span
      v-if="
        userId === row.user_id ||
        !$hasPermission(
          'group_user.update',
          row,
          column.additionalProps.groupId
        )
      "
    >
      {{ roleName(roles, row) }}
    </span>
    <a
      v-else
      ref="editRoleContextLink"
      @click="$refs.editRoleContext.toggle($refs.editRoleContextLink)"
    >
      {{ roleName(roles, row) }}
      <i class="fas fa-chevron-down"></i>
    </a>
    <EditRoleContext
      ref="editRoleContext"
      :subject="row"
      :roles="roles"
      role-value-column="role_uid"
      @update-role="roleUpdate($event)"
    ></EditRoleContext>
    <HelpIcon
      v-if="roleUidSelected === 'NO_ACCESS'"
      :tooltip="$t('membersRoleField.noAccessHelpText')"
      class="margin-left-1"
    />
    <HelpIcon
      v-if="roleUidSelected === 'ADMIN'"
      :tooltip="$t('membersRoleField.adminHelpText')"
      class="margin-left-1"
      is-warning
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { clone } from '@baserow/modules/core/utils/object'
import RoleAssignmentsService from '@baserow_enterprise/services/roleAssignments'
import EditRoleContext from '@baserow/modules/core/components/settings/members/EditRoleContext'
import { filterRoles } from '@baserow_enterprise/utils/roles'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'MembersRoleField',
  components: { EditRoleContext },
  props: {
    row: {
      type: Object,
      required: true,
    },
    column: {
      type: Object,
      required: true,
    },
  },
  computed: {
    group() {
      return this.$store.getters['group/get'](
        this.column.additionalProps.groupId
      )
    },
    roles() {
      return this.group
        ? filterRoles(this.group._.roles, {
            scopeType: 'group',
            subjectType: 'auth.User',
          })
        : []
    },
    roleUidSelected() {
      return this.row[this.column.key]
    },
    ...mapGetters({ userId: 'auth/getUserId' }),
  },
  methods: {
    roleName(roles, row) {
      const role = roles.find((r) => r.uid === row.role_uid)
      return role?.name || ''
    },
    async roleUpdate({ uid: permissionsNew, subject: member }) {
      const oldMember = clone(member)
      const newMember = clone(member)
      newMember.role_uid = permissionsNew
      this.$emit('row-update', newMember)

      try {
        await RoleAssignmentsService(this.$client).assignRole(
          newMember.user_id,
          'auth.User',
          this.column.additionalProps.groupId,
          this.column.additionalProps.groupId,
          'group',
          permissionsNew
        )
        this.$emit('refresh')
      } catch (error) {
        this.$emit('row-update', oldMember)
        notifyIf(error)
      }
    },
  },
}
</script>
