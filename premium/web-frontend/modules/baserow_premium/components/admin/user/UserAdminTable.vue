<template>
  <CrudTable
    :left-columns="leftColumns"
    :right-columns="rightColumns"
    :service="service"
    row-id-key="id"
    @edit-user="displayEditUserContext"
    @show-group="displayHiddenGroups"
    @row-context="onRowContext"
  >
    <template #header>
      <div class="crudtable__header-title">User Settings</div>
    </template>
    <template #menus="slotProps">
      <EditUserContext
        ref="editUserContext"
        :user="editUser"
        @delete-user="slotProps.deleteRow"
        @update="slotProps.updateRow"
      >
      </EditUserContext>
      <HiddenGroupsContext
        ref="hiddenGroupsContext"
        :hidden-groups="hiddenGroups"
      ></HiddenGroupsContext>
    </template>
  </CrudTable>
</template>

<script>
import UserAdminService from '@baserow_premium/services/userAdmin'
import UsernameField from '@baserow_premium/components/admin/user/fields/UsernameField'
import UserGroupsField from '@baserow_premium/components/admin/user/fields/UserGroupsField'
import CrudTable from '@baserow_premium/components/crud_table/CrudTable'
import SimpleField from '@baserow_premium/components/crud_table/fields/SimpleField'
import LocalDateField from '@baserow_premium/components/crud_table/fields/LocalDateField'
import ActiveField from '@baserow_premium/components/admin/user/fields/ActiveField'
import EditUserContext from '@baserow_premium/components/admin/user/contexts/EditUserContext'
import HiddenGroupsContext from '@baserow_premium/components/admin/user/contexts/HiddenGroupsContext'
import CrudTableColumn from '@baserow_premium/crud_table/CrudTableColumn'

export default {
  name: 'UserAdminTable',
  components: {
    HiddenGroupsContext,
    CrudTable,
    EditUserContext,
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
        'username',
        'Username',
        UsernameField,
        '200px',
        'max-content',
        true
      ),
    ]
    this.rightColumns = [
      new CrudTableColumn('name', 'Name', SimpleField, '100px', '200px', true),
      new CrudTableColumn(
        'groups',
        'Groups',
        UserGroupsField,
        '100px',
        '500px'
      ),
      new CrudTableColumn(
        'last_login',
        'Last Login',
        LocalDateField,
        'min-content',
        '200px',
        true
      ),
      new CrudTableColumn(
        'date_joined',
        'Signed Up',
        LocalDateField,
        'min-content',
        '200px',
        true
      ),
      new CrudTableColumn(
        'is_active',
        'Active',
        ActiveField,
        'min-content',
        '200px',
        true
      ),
    ]
    this.service = UserAdminService(this.$client)
    return {
      editUser: {},
      hiddenGroups: [],
    }
  },
  methods: {
    displayEditUserContext(event) {
      this.editUser = event.user
      this.$refs.editUserContext.show(event.target, 'bottom', 'left', 4)
    },
    onRowContext({ row, event }) {
      this.displayEditUserContext({
        user: row,
        target: {
          left: event.clientX,
          top: event.clientY,
        },
      })
    },
    displayHiddenGroups(event) {
      this.hiddenGroups = event.hiddenGroups
      this.$refs.hiddenGroupsContext.show(event.target, 'bottom', 'left', 4)
    },
  },
}
</script>
