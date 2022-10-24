<template>
  <Context>
    <template v-if="Object.keys(user).length > 0">
      <div class="context__menu-title">{{ user.username }} ({{ user.id }})</div>
      <ul class="context__menu">
        <li>
          <a @click.prevent="showEditModal">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            {{ $t('action.edit') }}
          </a>
        </li>
        <li>
          <a @click.prevent="showChangePasswordModal">
            <i class="context__menu-icon fas fa-fw fa-key"></i>
            {{ $t('editUserContext.changePassword') }}
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
            {{ $t('action.deactivate') }}
          </a>
          <a
            v-else
            :class="{
              'context__menu-item--loading': loading,
            }"
            @click.prevent="activate"
          >
            <i class="context__menu-icon fas fa-fw fa-check"></i>
            {{ $t('action.activate') }}
          </a>
        </li>
        <li v-if="user.id !== userId && !user.is_staff">
          <a
            :class="{
              'context__menu-item--loading': impersonateLoading,
            }"
            @click.prevent="impersonate"
          >
            <i class="context__menu-icon fas fa-fw fa-user-friends"></i>
            {{ $t('editUserContext.impersonate') }}
          </a>
        </li>
        <li>
          <a @click.prevent="showDeleteModal">
            <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
            {{ $t('editUserContext.delete') }}
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
import { mapGetters } from 'vuex'

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
      impersonateLoading: false,
    }
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
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
    impersonate() {
      this.impersonateLoading = true
      let url = this.$nuxt.$router.resolve({ name: 'dashboard' }).href
      // Adding the `__impersonate-user` query parameter impersonates the user when the
      // page first loads.
      url += '?__impersonate-user=' + this.user.id
      window.location.href = url
    },
  },
}
</script>
