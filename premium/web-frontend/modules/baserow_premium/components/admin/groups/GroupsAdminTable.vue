<template>
  <CrudTable
    :columns="columns"
    :service="service"
    row-id-key="id"
    @show-hidden-groups="displayHiddenUsers"
    @row-context="onRowContext"
  >
    <template #title>
      {{ $t('groupsAdminTable.allGroups') }}
    </template>
    <template #menus="slotProps">
      <EditGroupContext
        ref="editGroupContext"
        :group="editGroup"
        @group-deleted="slotProps.deleteRow"
      >
      </EditGroupContext>
      <HiddenUsersContext
        ref="hiddenUsersContext"
        :hidden-values="hiddenUsers"
      ></HiddenUsersContext>
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
import HiddenUsersContext from '@baserow_premium/components/admin/groups/contexts/HiddenUsersContext'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export default {
  name: 'GroupsAdminTable',
  components: {
    CrudTable,
    HiddenUsersContext,
    EditGroupContext,
  },
  data() {
    this.columns = [
      new CrudTableColumn(
        'name',
        () => this.$t('groupsAdminTable.name'),
        GroupNameField,
        true,
        true
      ),
      new CrudTableColumn(
        'users',
        () => this.$t('groupsAdminTable.members'),
        GroupUsersField
      ),
      new CrudTableColumn(
        'application_count',
        () => this.$t('groupsAdminTable.applications'),
        SimpleField,
        true
      ),
      new CrudTableColumn(
        'created_on',
        () => this.$t('groupsAdminTable.created'),
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
    displayHiddenUsers(event) {
      const action = this.hiddenUsers === event.hiddenValues ? 'toggle' : 'show'
      this.hiddenUsers = event.hiddenValues
      this.$refs.hiddenUsersContext[action](event.target, 'bottom', 'left', 4)
    },
  },
}
</script>
