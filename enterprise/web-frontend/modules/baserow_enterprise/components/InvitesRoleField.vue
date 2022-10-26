<template>
  <div>
    <a
      ref="editRoleContextLink"
      @click="$refs.editRoleContext.toggle($refs.editRoleContextLink)"
    >
      {{ $t(roleName(roles, row)) }}
      <i class="fas fa-chevron-down"></i>
    </a>
    <EditRoleContext
      ref="editRoleContext"
      :row="row"
      :roles="roles"
      role-value-column="permissions"
      @update-role="roleUpdate($event)"
    ></EditRoleContext>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import EditRoleContext from '@baserow/modules/core/components/settings/members/EditRoleContext'
import { clone } from '@baserow/modules/core/utils/object'
import GroupService from '@baserow/modules/core/services/group'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'InvitationsRoleField',
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
    ...mapGetters({ userId: 'auth/getUserId', roles: 'roles/getAllRoles' }),
  },
  methods: {
    roleName(roles, row) {
      const role = roles.find((r) => r.uid === row.permissions)
      return role?.name || ''
    },
    async roleUpdate({ uid: permissionsNew, row: invitation }) {
      const oldInvitation = clone(invitation)
      const newInvitation = clone(invitation)
      newInvitation.permissions = permissionsNew
      this.$emit('row-update', newInvitation)

      try {
        await GroupService(this.$client).updateInvitation(
          invitation.id,
          invitation
        )
      } catch (error) {
        this.$emit('row-update', oldInvitation)
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
