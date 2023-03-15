<template>
  <CrudTable
    :columns="columns"
    :service="service"
    row-id-key="id"
    @row-context="onRowContext"
  >
    <template #title>
      {{ $t('workspacesAdminTable.allWorkspaces') }}
    </template>
    <template #menus="slotProps">
      <EditGroupContext
        ref="editGroupContext"
        :group="editGroup"
        @group-deleted="slotProps.deleteRow"
      >
      </EditGroupContext>
    </template>
  </CrudTable>
</template>

<script>
import GroupsAdminService from '@baserow_premium/services/admin/groups'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import GroupUsersField from '@baserow_premium/components/admin/groups/fields/GroupUsersField'
import GroupNameField from '@baserow_premium/components/admin/groups/fields/GroupNameField'
import EditGroupContext from '@baserow_premium/components/admin/groups/contexts/EditGroupContext'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export default {
  name: 'GroupsAdminTable',
  components: {
    CrudTable,
    EditGroupContext,
  },
  data() {
    this.columns = [
      new CrudTableColumn(
        'name',
        () => this.$t('workspacesAdminTable.name'),
        GroupNameField,
        true,
        true
      ),
      new CrudTableColumn(
        'users',
        () => this.$t('workspacesAdminTable.members'),
        GroupUsersField
      ),
      new CrudTableColumn(
        'application_count',
        () => this.$t('workspacesAdminTable.applications'),
        SimpleField,
        true
      ),
      new CrudTableColumn(
        'free_users',
        () => this.$t('workspacesAdminTable.freeUsers'),
        SimpleField
      ),
      new CrudTableColumn(
        'seats_taken',
        () => this.$t('workspacesAdminTable.seatsTaken'),
        SimpleField,
        false,
        false,
        false,
        {},
        '',
        this.$t('workspacesAdminTable.usageHelpText')
      ),
      new CrudTableColumn(
        'row_count',
        () => this.$t('workspacesAdminTable.rowCount'),
        SimpleField,
        true,
        false,
        false,
        {},
        '',
        this.$t('workspacesAdminTable.usageHelpText')
      ),
      new CrudTableColumn(
        'storage_usage',
        () => this.$t('workspacesAdminTable.storageUsage'),
        SimpleField,
        true,
        false,
        false,
        {},
        '',
        this.$t('workspacesAdminTable.usageHelpText')
      ),
      new CrudTableColumn(
        'created_on',
        () => this.$t('workspacesAdminTable.created'),
        LocalDateField,
        true
      ),
      new CrudTableColumn('more', '', MoreField, false, false, true),
    ]
    this.service = GroupsAdminService(this.$client)
    return {
      editGroup: {},
      hiddenUsers: [],
    }
  },
  methods: {
    onRowContext({ row, event, target }) {
      event.preventDefault()
      if (target === undefined) {
        target = {
          left: event.clientX,
          top: event.clientY,
        }
      }

      const action = row.id === this.editGroup.id ? 'toggle' : 'show'
      this.editGroup = row
      this.$refs.editGroupContext[action](target, 'bottom', 'left', 4)
    },
  },
}
</script>
