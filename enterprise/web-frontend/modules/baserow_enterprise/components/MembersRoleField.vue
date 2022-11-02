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
      :row="row"
      :roles="roles"
      role-value-column="role_uid"
      @update-role="roleUpdate($event)"
    ></EditRoleContext>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'
import RoleAssignmentsService from '@baserow_enterprise/services/roleAssignments'
import EditRoleContext from '@baserow/modules/core/components/settings/members/EditRoleContext'

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
      return this.group ? this.group._.roles : []
    },
    ...mapGetters({ userId: 'auth/getUserId' }),
  },
  methods: {
    roleName(roles, row) {
      const role = roles.find((r) => r.uid === row.role_uid)
      return role?.name || ''
    },
    async roleUpdate({ uid: permissionsNew, row: member }) {
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
      } catch (error) {
        this.$emit('row-update', oldMember)
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
