<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :columns="columns"
      row-id-key="id"
      @row-context="onRowContext"
      @edit-role-context="onEditRoleContext"
    >
      <template #title>
        {{
          $t('membersSettings.membersTable.title', {
            userAmount: group.users.length || 0,
            groupName: group.name,
          })
        }}
      </template>
      <template #header-right-side>
        <div
          class="button margin-left-2 button--large"
          @click="$refs.inviteModal.show()"
        >
          {{ $t('membersSettings.membersTable.inviteMember') }}
        </div>
      </template>
      <template #menus>
        <EditMemberContext
          ref="editMemberContext"
          :group="group"
          :member="editMember"
          @refresh="refresh"
        ></EditMemberContext>
        <EditRoleContext
          ref="editRoleContext"
          :row="editRoleMember"
          :roles="roles"
          @update-role="roleUpdate($event)"
        ></EditRoleContext>
      </template>
    </CrudTable>
    <GroupMemberInviteModal
      ref="inviteModal"
      :group="group"
      @invite-submitted="
        $router.push({
          name: 'settings-invites',
          params: {
            groupId: group.id,
          },
        })
      "
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'

import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import GroupService from '@baserow/modules/core/services/group'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import MemberRoleField from '@baserow/modules/core/components/settings/members/MemberRoleField'
import GroupMemberInviteModal from '@baserow/modules/core/components/group/GroupMemberInviteModal'
import EditMemberContext from '@baserow/modules/core/components/settings/members/EditMemberContext'
import EditRoleContext from '@baserow/modules/core/components/settings/members/EditRoleContext'

export default {
  name: 'MembersTable',
  components: {
    EditMemberContext,
    EditRoleContext,
    CrudTable,
    GroupMemberInviteModal,
  },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      editMember: {},
      editRoleMember: {},
    }
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
    roles() {
      return this.$store.getters['roles/getAllRoles'].map(
        ({ uid, name, description }) => ({
          uid,
          name: this.$t(name),
          description: this.$t(description),
        })
      )
    },
    service() {
      const service = GroupService(this.$client)
      const options = {
        ...service.options,
        urlParams: { groupId: this.group.id },
      }
      return {
        ...service,
        options,
      }
    },
    membersPagePlugins() {
      return Object.values(this.$registry.getAll('membersPagePlugins'))
    },
    columns() {
      let columns = [
        new CrudTableColumn(
          'name',
          this.$t('membersSettings.membersTable.columns.name'),
          SimpleField,
          true,
          true
        ),
        new CrudTableColumn(
          'email',
          this.$t('membersSettings.membersTable.columns.email'),
          SimpleField,
          true
        ),
        new CrudTableColumn(
          'permissions',
          this.$t('membersSettings.membersTable.columns.role'),
          MemberRoleField,
          false,
          false,
          false,
          {
            roles: this.roles,
            userId: this.userId,
          }
        ),
        new CrudTableColumn(null, null, MoreField, false, false, true),
      ]
      for (const plugin of this.membersPagePlugins) {
        if (!plugin.isDeactivated()) {
          columns = plugin.mutateMembersTableColumns(columns, {
            group: this.group,
            client: this.$client,
          })
        }
      }
      return columns
    },
  },
  methods: {
    onRowContext({ row, event, target }) {
      if (target === undefined) {
        target = {
          left: event.clientX,
          top: event.clientY,
        }
      }

      const action = row.id === this.editMember.id ? 'toggle' : 'show'
      this.editMember = row
      this.$refs.editMemberContext[action](target, 'bottom', 'left', 4)
    },
    onEditRoleContext({ row, target }) {
      const action = row.id === this.editRoleMember.id ? 'toggle' : 'show'
      this.editRoleMember = row
      this.$refs.editRoleContext[action](target, 'bottom', 'left', 4)
    },
    async refresh() {
      await this.$refs.crudTable.fetch()
    },
    async roleUpdate({ uid: permissionsNew, row: member }) {
      const oldMember = clone(member)
      const newMember = clone(member)
      newMember.permissions = permissionsNew
      this.$refs.crudTable.updateRow(newMember)

      try {
        await GroupService(this.$client).updateUser(oldMember.id, {
          permissions: newMember.permissions,
        })
        await this.$store.dispatch('group/forceUpdateGroupUser', {
          groupId: this.group.id,
          id: oldMember.id,
          values: { permissions: newMember.permissions },
        })
      } catch (error) {
        this.$refs.crudTable.updateRow(oldMember)
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
