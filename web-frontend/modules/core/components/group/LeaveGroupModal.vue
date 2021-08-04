<template>
  <Modal>
    <h2 class="box__title">Leave {{ group.name }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure you want to leave the group
        <strong>{{ group.name }}</strong
        >? You won't be able to access the related applications anymore and if
        you want to regain access, one of the admins must invite you again. If
        you leave the group, it will not be deleted. All the other members will
        still have access to it. It is not possible to leave a group if you're
        the last admin because that will leave it unmaintained.
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="leaveGroup()"
          >
            Leave group
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
