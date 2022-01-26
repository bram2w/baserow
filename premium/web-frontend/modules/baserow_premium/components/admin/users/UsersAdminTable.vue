<template>
  <CrudTable
    :left-columns="leftColumns"
    :right-columns="rightColumns"
    :service="service"
    row-id-key="id"
    @edit-user="displayEditUserContext"
    @show-hidden-groups="displayHiddenGroups"
    @row-context="onRowContext"
  >
    <template #header>
      <div class="crudtable__header-title">
        {{ $t('usersAdminTable.allUsers') }}
      </div>
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
        :hidden-values="hiddenGroups"
      ></HiddenGroupsContext>
    </template>
  </CrudTable>
</template>

<script>
import UserAdminService from '@baserow_premium/services/admin/users'
import UsernameField from '@baserow_premium/components/admin/users/fields/UsernameField'
import UserGroupsField from '@baserow_premium/components/admin/users/fields/UserGroupsField'
import CrudTable from '@baserow_premium/components/crud_table/CrudTable'
import SimpleField from '@baserow_premium/components/crud_table/fields/SimpleField'
import LocalDateField from '@baserow_premium/components/crud_table/fields/LocalDateField'
import ActiveField from '@baserow_premium/components/admin/users/fields/ActiveField'
import EditUserContext from '@baserow_premium/components/admin/users/contexts/EditUserContext'
import HiddenGroupsContext from '@baserow_premium/components/admin/users/contexts/HiddenGroupsContext'
import CrudTableColumn from '@baserow_premium/crud_table/crudTableColumn'

export default {
  name: 'UsersAdminTable',
  components: {
    HiddenGroupsContext,
    CrudTable,
    EditUserContext,
  },
  data() {
    this.leftColumns = [
      new CrudTableColumn(
        'id',
        () => this.$t('usersAdminTable.id'),
        SimpleField,
        'min-content',
        'max-content',
        true
      ),
      new CrudTableColumn(
        'username',
        () => this.$t('usersAdminTable.username'),
        UsernameField,
        '200px',
        'max-content',
        true
      ),
    ]
    this.rightColumns = [
      new CrudTableColumn(
        'name',
        () => this.$t('usersAdminTable.name'),
        SimpleField,
        '100px',
        '200px',
        true
      ),
      new CrudTableColumn(
        'groups',
        () => this.$t('usersAdminTable.groups'),
        UserGroupsField,
        '100px',
        '500px'
      ),
      new CrudTableColumn(
        'last_login',
        () => this.$t('usersAdminTable.lastLogin'),
        LocalDateField,
        'min-content',
        '200px',
        true
      ),
      new CrudTableColumn(
        'date_joined',
        () => this.$t('usersAdminTable.dateJoined'),
        LocalDateField,
        'min-content',
        '200px',
        true
      ),
      new CrudTableColumn(
        'is_active',
        () => this.$t('premium.user.active'),
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
      const action = event.user.id === this.editUser.id ? 'toggle' : 'show'
      this.editUser = event.user
      this.$refs.editUserContext[action](event.target, 'bottom', 'left', 4)
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
      const action =
        this.hiddenGroups === event.hiddenValues ? 'toggle' : 'show'
      this.hiddenGroups = event.hiddenValues
      this.$refs.hiddenGroupsContext[action](event.target, 'bottom', 'left', 4)
    },
  },
}
</script>
