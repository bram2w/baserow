<template>
  <CrudTable
    :left-columns="leftColumns"
    :right-columns="rightColumns"
    :service="service"
    row-id-key="id"
    @edit-group="displayEditGroupContext"
    @show-hidden-groups="displayHiddenUsers"
    @row-context="onRowContext"
  >
    <template #header>
      <div class="crudtable__header-title">All groups</div>
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
import CrudTable from '@baserow_premium/components/crud_table/CrudTable'
import SimpleField from '@baserow_premium/components/crud_table/fields/SimpleField'
import LocalDateField from '@baserow_premium/components/crud_table/fields/LocalDateField'
import GroupUsersField from '@baserow_premium/components/admin/groups/fields/GroupUsersField'
import GroupNameField from '@baserow_premium/components/admin/groups/fields/GroupNameField'
import EditGroupContext from '@baserow_premium/components/admin/groups/contexts/EditGroupContext'
import HiddenUsersContext from '@baserow_premium/components/admin/groups/contexts/HiddenUsersContext'
import CrudTableColumn from '@baserow_premium/crud_table/crudTableColumn'

export default {
  name: 'GroupsAdminTable',
  components: {
    CrudTable,
    HiddenUsersContext,
    EditGroupContext,
  },
  data() {
    this.leftColumns = [
      new CrudTableColumn(
        'id',
        'ID',
        SimpleField,
        'min-content',
        'max-content',
        true
      ),
      new CrudTableColumn(
        'name',
        'Name',
        GroupNameField,
        '200px',
        'max-content',
        true
      ),
    ]
    this.rightColumns = [
      new CrudTableColumn(
        'users',
        'Members',
        GroupUsersField,
        '100px',
        '500px'
      ),
      new CrudTableColumn(
        'application_count',
        'Applications',
        SimpleField,
        'min-content',
        'max-content',
        true
      ),
      new CrudTableColumn(
        'created_on',
        'Created',
        LocalDateField,
        'min-content',
        '200px',
        true
      ),
    ]
    this.service = GroupsAdminService(this.$client)
    return {
      editGroup: {},
      hiddenUsers: [],
    }
  },
  methods: {
    displayEditGroupContext(event) {
      const action = event.group.id === this.editGroup.id ? 'toggle' : 'show'
      this.editGroup = event.group
      this.$refs.editGroupContext[action](event.target, 'bottom', 'left', 4)
    },
    onRowContext({ row, event }) {
      this.displayEditGroupContext({
        group: row,
        target: {
          left: event.clientX,
          top: event.clientY,
        },
      })
    },
    displayHiddenUsers(event) {
      const action = this.hiddenUsers === event.hiddenValues ? 'toggle' : 'show'
      this.hiddenUsers = event.hiddenValues
      this.$refs.hiddenUsersContext[action](event.target, 'bottom', 'left', 4)
    },
  },
}
</script>
