<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('leaveGroupModal.title', { group: group.name }) }}
    </h2>
    <Error :error="error"></Error>
    <div>
      <p>
        {{ $t('leaveGroupModal.message', { group: group.name }) }}
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="leaveGroup()"
          >
            {{ $t('leaveGroupModal.leave') }}
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'LeaveGroupModal',
  mixins: [modal, error],
  props: {
    group: {
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
    async leaveGroup() {
      this.hideError()
      this.loading = true

      try {
        await this.$store.dispatch('group/leave', this.group)
        this.hide()
      } catch (error) {
        this.handleError(error, 'view')
      }

      this.loading = false
    },
  },
}
</script>

<i18n>
{
  "en": {
    "leaveGroupModal": {
      "title": "Leave {group}",
      "message": "Are you sure you want to leave the group {group}? You won't be able to access the related applications anymore and if you want to regain access, one of the admins must invite you again. If you leave the group, it will not be deleted. All the other members will still have access to it. It is not possible to leave a group if you're the last admin because that will leave it unmaintained.",
      "leave": "Leave group"
    }
  },
  "fr": {
    "leaveGroupModal": {
      "title": "Quitter {groupe}",
      "message": "Êtes-vous sûr·e de vouloir quitter le groupe {group} ? Vous ne serez plus en mesure d'accéder aux applications associées et si vous souhaitez y accéder de nouveau, l'un des administrateurs du groupe devra vous envoyer une nouvelle invitation. Si vous quittez un groupe, celui-ci ne sera pas supprimé et les autres membres y auront toujours accès. Il n'est pas possible de quitter un groupe si vous êtes le dernier administrateur car il se retrouverait alors sans propriétaire.",
      "leave": "Quitter le groupe"
    }
  }
}
</i18n>
