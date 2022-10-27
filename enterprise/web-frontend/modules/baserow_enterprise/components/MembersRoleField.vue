<template>
  <div>
    <span v-if="userId === row.user_id">
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
      role-value-column="permissions"
      @update-role="roleUpdate($event)"
    ></EditRoleContext>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'
import EditRoleContext from '@baserow/modules/core/components/settings/members/EditRoleContext'
import GroupService from '@baserow/modules/core/services/group'

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
    ...mapGetters({ userId: 'auth/getUserId', roles: 'roles/getAllRoles' }),
  },
  methods: {
    roleName(roles, row) {
      const role = roles.find((r) => r.uid === row.permissions)
      return role?.name || ''
    },
    async roleUpdate({ uid: permissionsNew, row: member }) {
      const oldMember = clone(member)
      const newMember = clone(member)
      newMember.permissions = permissionsNew
      this.$emit('row-update', newMember)

      try {
        await GroupService(this.$client).updateUser(oldMember.id, {
          permissions: newMember.permissions,
        })
        await this.$store.dispatch('group/forceUpdateGroupUser', {
          groupId: this.column.additionalProps.groupId,
          id: oldMember.id,
          values: { permissions: newMember.permissions },
        })
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
