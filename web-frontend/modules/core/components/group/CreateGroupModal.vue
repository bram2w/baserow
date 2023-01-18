<template>
  <Modal>
    <h2 class="box__title">{{ $t('createGroupModal.createNew') }}</h2>
    <Error :error="error"></Error>
    <GroupForm
      ref="groupForm"
      :default-name="getDefaultName()"
      @submitted="submitted"
    >
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
import { getNextAvailableNameInSequence } from '@baserow/modules/core/utils/string'

import GroupForm from './GroupForm'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'

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
    getDefaultName() {
      const excludeNames = this.$store.getters['group/getAll'].map(
        (group) => group.name
      )
      const baseName = this.$t('createGroupModal.defaultName')
      return getNextAvailableNameInSequence(baseName, excludeNames)
    },
    async submitted(values) {
      this.loading = true
      this.hideError()

      try {
        const group = await this.$store.dispatch('group/create', values)
        await this.$store.dispatch('group/select', group)
        this.loading = false
        this.$emit('created', group)
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'group')
        this.handleError(error, 'group', {
          PERMISSION_DENIED: new ResponseErrorMessage(
            this.$t('createGroupModal.permissionDeniedTitle'),
            this.$t('createGroupModal.permissionDeniedBody')
          ),
        })
      }
    },
  },
}
</script>
