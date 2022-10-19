<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :left-columns="leftColumns"
      :right-columns="rightColumns"
      row-id-key="id"
      @remove="remove"
      @copy-email="copyEmail"
    >
      <template #header-left-side>
        <div class="crudtable__header-title">
          {{
            $t('membersSettings.membersTable.title', {
              userAmount: group.users.length || 0,
              groupName: group.name,
            })
          }}
        </div>
      </template>
      <template #header-right-side>
        <div class="button margin-left-1" @click="$refs.inviteModal.show()">
          {{ $t('membersSettings.membersTable.inviteMember') }}
        </div>
      </template>
    </CrudTable>
    <MembersInviteModal
      ref="inviteModal"
      :group="group"
      @invite-submitted="$emit('invite-submitted', $event)"
    />
  </div>
</template>

<script>
import CrudTable from '@baserow/modules/core/components/crud_table/CrudTable'
import GroupService from '@baserow/modules/core/services/group'
import { mapGetters } from 'vuex'
import CrudTableColumn from '@baserow/modules/core/crud_table/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crud_table/fields/SimpleField'
import DropdownField from '@baserow/modules/core/components/crud_table/fields/DropdownField'
import { notifyIf } from '@baserow/modules/core/utils/error'
import MembersInviteModal from '@baserow/modules/core/components/settings/members/MembersInviteModal'
import ActionsField from '@baserow/modules/core/components/crud_table/fields/ActionsField'

export default {
  name: 'MembersTable',
  components: { CrudTable, MembersInviteModal },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
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
    leftColumns() {
      return [
        new CrudTableColumn(
          'name',
          this.$t('membersSettings.membersTable.columns.name'),
          SimpleField,
          'min-content',
          '2fr',
          true
        ),
      ]
    },
    rightColumns() {
      return [
        new CrudTableColumn(
          'email',
          this.$t('membersSettings.membersTable.columns.email'),
          SimpleField,
          'min-content',
          '3fr',
          true
        ),
        new CrudTableColumn(
          'permissions',
          this.$t('membersSettings.membersTable.columns.role'),
          DropdownField,
          'min-content',
          '3fr',
          true,
          {
            options: [
              {
                value: 'ADMIN',
                name: this.$t('permission.admin'),
                description: this.$t('permission.adminDescription'),
              },
              {
                value: 'MEMBER',
                name: this.$t('permission.member'),
                description: this.$t('permission.memberDescription'),
              },
            ],
            disabled: (row) => row.user_id === this.userId,
            inputCallback: this.roleUpdate,
            action: {
              label: this.$t('membersSettings.membersTable.actions.remove'),
              colorClass: 'color--deep-dark-red',
              onClickEventName: 'remove',
            },
          }
        ),
        new CrudTableColumn(
          null,
          null,
          ActionsField,
          'min-content',
          'min-content',
          false,
          {
            actions: [
              {
                label: this.$t(
                  'membersSettings.membersTable.actions.copyEmail'
                ),
                onClickEventName: 'copy-email',
              },
              {
                label: this.$t('membersSettings.membersTable.actions.remove'),
                onClickEventName: 'remove',
                disabled: (row) => row.user_id === this.userId,
                colorClass: 'color--deep-dark-red',
              },
            ],
          }
        ),
      ]
    },
  },
  methods: {
    async roleUpdate(permissionsNew, { permissions, id }) {
      if (permissions === permissionsNew) {
        return
      }

      try {
        await GroupService(this.$client).updateUser(id, {
          permissions: permissionsNew,
        })
        await this.$store.dispatch('group/forceUpdateGroupUser', {
          groupId: this.group.id,
          id,
          values: { permissions: permissionsNew },
        })
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
    async copyEmail({ email }) {
      await navigator.clipboard.writeText(email)
      await this.$store.dispatch('notification/add', {
        type: 'success',
        title: this.$t('membersSettings.membersTable.copiedEmail.title'),
        message: this.$t('membersSettings.membersTable.copiedEmail.message'),
      })
    },
    async remove(user) {
      try {
        await GroupService(this.$client).deleteUser(user.id)
        await this.$store.dispatch('group/forceDeleteGroupUser', {
          groupId: this.group.id,
          id: user.id,
          values: { user_id: this.userId },
        })
        await this.$refs.crudTable.fetch()
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
