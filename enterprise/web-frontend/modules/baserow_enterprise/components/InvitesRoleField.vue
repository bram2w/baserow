<template>
  <div>
    <a
      ref="editRoleContextLink"
      @click="$refs.editRoleContext.toggle($refs.editRoleContextLink)"
    >
      {{ roleName(roles, rowSanitised) }}
      <i class="fas fa-chevron-down"></i>
    </a>
    <EditRoleContext
      ref="editRoleContext"
      :row="rowSanitised"
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
    ...mapGetters({ userId: 'auth/getUserId' }),
    group() {
      return this.$store.getters['group/get'](
        this.column.additionalProps.groupId
      )
    },
    roles() {
      return this.group ? this.group._.roles : []
    },
    rowSanitised() {
      return {
        ...this.row,
        permissions: this.roles.some(({ uid }) => uid === this.row.permissions)
          ? this.row.permissions
          : 'BUILDER',
      }
    },
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
          newInvitation.id,
          newInvitation
        )
      } catch (error) {
        this.$emit('row-update', oldInvitation)
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
