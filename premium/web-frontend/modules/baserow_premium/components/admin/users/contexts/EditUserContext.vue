<template>
  <Context>
    <template v-if="Object.keys(user).length > 0">
      <ul class="context__menu">
        <li>
          <a @click.prevent="showEditModal">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            Edit
          </a>
        </li>
        <li>
          <a @click.prevent="showChangePasswordModal">
            <i class="context__menu-icon fas fa-fw fa-key"></i>
            Change password
          </a>
        </li>
        <li>
          <a
            v-if="user.is_active"
            :class="{
              'context__menu-item--loading': loading,
            }"
            @click.prevent="deactivate"
          >
            <i class="context__menu-icon fas fa-fw fa-times"></i>
            Deactivate
          </a>
          <a
            v-else
            :class="{
              'context__menu-item--loading': loading,
            }"
            @click.prevent="activate"
          >
            <i class="context__menu-icon fas fa-fw fa-check"></i>
            Activate
          </a>
        </li>
        <li>
          <a @click.prevent="showDeleteModal">
            <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
            Permanently delete
          </a>
        </li>
      </ul>
      <DeleteUserModal
        ref="deleteUserModal"
        :user="user"
        @delete-user="onDeleteUser"
      ></DeleteUserModal>
      <EditUserModal
        ref="editUserModal"
        :user="user"
        @update="$emit('update', $event)"
        @delete-user="onDeleteUser"
      >
      </EditUserModal>
      <ChangePasswordModal
        ref="changePasswordModal"
        :user="user"
      ></ChangePasswordModal>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ChangePasswordModal from '@baserow_premium/components/admin/users/modals/ChangeUserPasswordModal'
import DeleteUserModal from '@baserow_premium/components/admin/users/modals/DeleteUserModal'
import EditUserModal from '@baserow_premium/components/admin/users/modals/EditUserModal'
import UserAdminService from '@baserow_premium/services/admin/users'

export default {
  name: 'EditUserContext',
  components: {
    ChangePasswordModal,
    DeleteUserModal,
    EditUserModal,
  },
  mixins: [context],
  props: {
    user: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    showChangePasswordModal() {
      this.hide()
      this.$refs.changePasswordModal.show()
    },
    showDeleteModal() {
      this.hide()
      this.$refs.deleteUserModal.show()
    },
    showEditModal() {
      this.hide()
      this.$refs.editUserModal.show()
    },
    onDeleteUser(event) {
      this.$emit('delete-user', event)
      this.$refs.editUserModal.hide()
    },
    async changeIsActive(isActive) {
      try {
        this.loading = true
        const { data: newUser } = await UserAdminService(this.$client).update(
          this.user.id,
          { is_active: isActive }
        )

        this.hide()
        this.$emit('update', newUser)
      } catch (error) {
        notifyIf(error, 'settings')
      }
      this.loading = false
    },
    async activate() {
      await this.changeIsActive(true)
    },
    async deactivate() {
      await this.changeIsActive(false)
    },
  },
}
</script>
