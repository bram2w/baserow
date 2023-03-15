<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('leaveWorkspaceModal.title', { workspace: group.name }) }}
    </h2>
    <Error :error="error"></Error>
    <div>
      <p>
        {{ $t('leaveWorkspaceModal.message', { workspace: group.name }) }}
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="leaveGroup()"
          >
            {{ $t('leaveWorkspaceModal.leave') }}
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
