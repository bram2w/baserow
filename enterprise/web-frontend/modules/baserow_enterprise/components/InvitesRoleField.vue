<template>
  <div>
    <a
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
      role-value-column="permissions"
      @update-role="roleUpdate($event)"
    ></EditRoleContext>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { roles } from '@baserow_enterprise/enums/roles'
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
    ...mapGetters({ userId: 'auth/getUserId' }),
    roles() {
      return roles.map(({ name, uid }) => ({
        value: uid,
        name,
      }))
    },
  },
  methods: {
    roleName(roles, row) {
      const role = roles.find((r) => r.value === row.permissions)
      return role?.name || ''
    },
    async roleUpdate({ value: permissionsNew, row: invitation }) {
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
