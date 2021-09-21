<template>
  <Modal>
    <h2 class="box__title">{{ $t('createGroupModal.createNew') }}</h2>
    <Error :error="error"></Error>
    <GroupForm ref="groupForm" @submitted="submitted">
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('createGroupModal.add') }}
          </button>
        </div>
      </div>
    </GroupForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

import GroupForm from './GroupForm'

export default {
  name: 'CreateGroupModal',
  components: { GroupForm },
  mixins: [modal, error],
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async submitted(values) {
      this.loading = true
      this.hideError()

      try {
        await this.$store.dispatch('group/create', values)
        this.loading = false
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'group')
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "createGroupModal": {
      "createNew": "Create new group",
      "add": "Add group"
    }
  },
  "fr": {
    "createGroupModal": {
      "createNew": "Nouveau groupe",
      "add": "Ajouter le groupe"
    }
  }
}
</i18n>
