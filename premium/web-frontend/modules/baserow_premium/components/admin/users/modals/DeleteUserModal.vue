<template>
  <Modal>
    <h2 class="box__title">{{ $t('deleteUserModal.title', user) }}</h2>
    <Error :error="error"></Error>
    <div>
      <i18n path="deleteUserModal.confirmation" tag="p">
        <template #name>
          <strong class="user-admin-delete__strong">{{ user.username }}</strong>
        </template>
      </i18n>
      <p>
        {{ $t('deleteUserModal.comment1') }}
      </p>
      <p>
        {{ $t('deleteUserModal.comment2') }}
      </p>
      <div class="actions">
        <div class="align-right">
          <a
            class="button button--large button--error button--overflow"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            :title="user.username"
            @click.prevent="deleteUser()"
          >
            {{ $t('deleteUserModal.delete', user) }}
          </a>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import UserAdminService from '@baserow_premium/services/admin/users'

export default {
  name: 'DeleteUserModal',
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
    async deleteUser() {
      this.hideError()
      this.loading = true

      try {
        await UserAdminService(this.$client).delete(this.user.id)
        this.$emit('delete-user', this.user.id)
        this.hide()
      } catch (error) {
        this.handleError(error, 'application')
      }

      this.loading = false
    },
  },
}
</script>

<i18n>
{
  "en": {
    "deleteUserModal": {
      "title": "Delete {username}",
      "confirmation": "Are you sure you want to delete the user: {name}?",
      "comment1":"The user account will be deleted, however the groups that user is a member of will continue existing. The users group will not be deleted, even if this user is the last user in the group. Deleting the last user in a group prevents anyone being able to access that group.",
      "comment2":"After deleting a user it is possible for a new user to sign up again using the deleted users email address. To ensure they cannot sign up again instead deactivate the user and do not delete them.",
      "delete": "Delete user {username}"
    }
  },
  "fr": {
    "deleteUserModal": {
      "title": "Supprimer {username}",
      "confirmation": "Êtes-vous sûr·e de vouloir supprimer l'utilisateur : {name} ?",      
      "comment1":"Le compte de l'utilisateur va être supprimé, cependant les groupes dont l'utilisateur est membre vont continuer d'exister. Ces groupes ne seront pas supprimés même si cet utilisateur est le dernier utilisateur du groupe. Supprimer le dernier utilisateur d'un groupe interdit à quiconque d'y accéder de nouveau.",
      "comment2":"Après avoir supprimé un utilisateur, il sera possible de créer un nouveau compte avec la même adresse email. Si vous souhaitez éviter que l'utilisateur puisse se connecter avec cette adresse, vous pouvez désactiver l'utilisateur plutôt que supprimer son compte.",
      "delete": "Supprimer l'utilisateur {username}"
    }
  }
}
</i18n>
