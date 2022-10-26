<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :columns="columns"
      row-id-key="id"
      @rows-update="invitesAmount = $event.length"
      @row-context="onRowContext"
      @edit-role-context="onEditRoleContext"
    >
      <template #title>
        {{
          $t('membersSettings.invitesTable.title', {
            invitesAmount,
            groupName: group.name,
          })
        }}
      </template>
      <template #header-right-side>
        <div
          class="button button--large margin-left-2"
          @click="$refs.inviteModal.show()"
        >
          {{ $t('membersSettings.membersTable.inviteMember') }}
        </div>
      </template>
      <template #menus>
        <EditInviteContext
          ref="editInviteContext"
          :invitation="editInvitation"
          @refresh="$refs.crudTable.fetch()"
        ></EditInviteContext>
        <EditRoleContext
          ref="editRoleContext"
          :group="group"
          :row="editRoleInvitation"
          :roles="roles"
          @update-role="roleUpdate($event)"
        ></EditRoleContext>
      </template>
    </CrudTable>
    <GroupMemberInviteModal
      ref="inviteModal"
      :group="group"
      @invite-submitted="$refs.crudTable.fetch()"
    />
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import GroupService from '@baserow/modules/core/services/group'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import GroupMemberInviteModal from '@baserow/modules/core/components/group/GroupMemberInviteModal'
import EditInviteContext from '@baserow/modules/core/components/settings/members/EditInviteContext'
import MemberRoleField from '@baserow/modules/core/components/settings/members/MemberRoleField'
import EditRoleContext from '@baserow/modules/core/components/settings/members/EditRoleContext'
import { clone } from '@baserow/modules/core/utils/object'

export default {
  name: 'MembersInvitesTable',
  components: {
    EditInviteContext,
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
      editInvitation: {},
      editRoleInvitation: {},
      invitesAmount: 0,
    }
  },
  computed: {
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

      service.options.baseUrl = ({ groupId }) =>
        `/groups/invitations/group/${groupId}/`

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
          'email',
          this.$t('membersSettings.invitesTable.columns.email'),
          SimpleField,
          true,
          true
        ),
        new CrudTableColumn(
          'message',
          this.$t('membersSettings.invitesTable.columns.message'),
          SimpleField,
          true
        ),
        new CrudTableColumn(
          'permissions',
          this.$t('membersSettings.invitesTable.columns.role'),
          MemberRoleField,
          false,
          false,
          false,
          {
            roles: this.roles,
            userId: 0,
          }
        ),
        new CrudTableColumn(null, null, MoreField, false, false, true),
      ]
      for (const plugin of this.membersPagePlugins) {
        if (!plugin.isDeactivated()) {
          columns = plugin.mutateMembersInvitesTableColumns(columns, {
            group: this.group,
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

      const action = row.id === this.editInvitation.id ? 'toggle' : 'show'
      this.editInvitation = row
      this.$refs.editInviteContext[action](target, 'bottom', 'left', 4)
    },
    onEditRoleContext({ row, target }) {
      const action = row.id === this.editRoleInvitation.id ? 'toggle' : 'show'
      this.editRoleInvitation = row
      this.$refs.editRoleContext[action](target, 'bottom', 'left', 4)
    },
    async roleUpdate({ uid: permissionsNew, row: invitation }) {
      const oldInvitation = clone(invitation)
      const newInvitation = clone(invitation)
      newInvitation.permissions = permissionsNew
      this.$refs.crudTable.updateRow(newInvitation)

      try {
        await GroupService(this.$client).updateInvitation(invitation.id, {
          permissions: permissionsNew,
        })
      } catch (error) {
        this.$refs.crudTable.updateRow(oldInvitation)
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
