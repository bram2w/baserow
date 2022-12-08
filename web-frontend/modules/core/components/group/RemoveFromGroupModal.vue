<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('removeFromGroupModal.title') }}
    </h2>
    <Error :error="error"></Error>
    <div>
      <p>
        {{
          $t('removeFromGroupModal.confirmation', {
            name: member.name,
            group_name: group.name,
          })
        }}
      </p>
      <div class="actions">
        <div class="align-right">
          <a
            class="button button--large button--error button--overflow"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click.prevent="remove()"
          >
            {{ $t('removeFromGroupModal.remove') }}
          </a>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import GroupService from '@baserow/modules/core/services/group'

export default {
  name: 'RemoveFromGroupModal',
  mixins: [modal, error],
  props: {
    group: {
      type: Object,
      required: true,
    },
    member: {
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
    async remove() {
      if (this.loading) {
        return
      }
      this.loading = true
      try {
        await GroupService(this.$client).deleteUser(this.member.id)
        await this.$store.dispatch('group/forceDeleteGroupUser', {
          groupId: this.group.id,
          id: this.member.id,
          values: { user_id: this.member.user_id },
        })
        this.$emit('remove-user', this.member.id)
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error)
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
