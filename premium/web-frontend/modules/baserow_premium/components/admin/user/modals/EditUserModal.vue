<template>
  <Modal>
    <h2 class="box__title">Edit {{ user.username }}</h2>
    <Error :error="error"></Error>
    <UserForm
      ref="form"
      :user="user"
      :loading="loading"
      :default-values="user"
      @submitted="editUser"
    >
      <div class="align-left">
        <a
          class="user-admin-edit__delete"
          @click="$refs.deleteUserModal.show()"
        >
          Delete User
        </a>
      </div>
    </UserForm>
    <DeleteUserModal
      ref="deleteUserModal"
      :user="user"
      @delete-user="$emit('delete-user', $event)"
    ></DeleteUserModal>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import UserAdminService from '@baserow_premium/services/userAdmin'
import UserForm from '@baserow_premium/components/admin/user/forms/UserForm'
import DeleteUserModal from '@baserow_premium/components/admin/user/modals/DeleteUserModal'

export default {
  name: 'EditUserModal',
  components: { DeleteUserModal, UserForm },
  mixins: [modal, error],
  props: {
    user: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async editUser(values) {
      this.loading = true
      this.hideError()

      try {
        const { data: userData } = await UserAdminService(this.$client).update(
          this.user.id,
          values
        )
        this.$emit('update', userData)
        this.loading = false
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'application')
      }
    },
  },
}
</script>
