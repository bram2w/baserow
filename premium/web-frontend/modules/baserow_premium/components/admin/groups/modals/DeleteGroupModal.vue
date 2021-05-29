<template>
  <Modal>
    <h2 class="box__title">Delete {{ group.name }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure you want to delete the group:
        <strong>{{ group.name }}</strong
        >?
      </p>
      <p>
        The group will be permanently deleted, including the related
        applications. It is not possible to undo this action.
      </p>
      <div class="actions">
        <div class="align-right">
          <a
            class="button button--large button--error button--overflow"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            :title="group.name"
            @click.prevent="deleteGroup()"
          >
            Delete group {{ group.name }}
          </a>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import GroupsAdminService from '@baserow_premium/services/admin/groups'

export default {
  name: 'DeleteGroupModal',
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
    async deleteGroup() {
      this.hideError()
      this.loading = true

      try {
        await GroupsAdminService(this.$client).delete(this.group.id)
        this.$emit('group-deleted', this.group.id)
        this.hide()
      } catch (error) {
        this.handleError(error, 'group')
      }

      this.loading = false
    },
  },
}
</script>
