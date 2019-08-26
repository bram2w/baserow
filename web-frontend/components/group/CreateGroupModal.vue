<template>
  <Modal>
    <h2 class="box-title">Create new group</h2>
    <GroupForm ref="groupForm" @submitted="submitted">
      <div class="actions">
        <div class="align-right">
          <button
            class="button button-large"
            :class="{ 'button-loading': loading }"
            :disabled="loading"
          >
            Add group
          </button>
        </div>
      </div>
    </GroupForm>
  </Modal>
</template>

<script>
import GroupForm from './GroupForm'

import modal from '@/mixins/modal'

export default {
  name: 'CreateGroupModal',
  components: { GroupForm },
  mixins: [modal],
  data() {
    return {
      loading: false
    }
  },
  methods: {
    submitted(values) {
      this.loading = true
      this.$store
        .dispatch('group/create', values)
        .then(() => {
          this.loading = false
          this.hide()
        })
        .catch(() => {
          this.loading = false
        })
    }
  }
}
</script>
