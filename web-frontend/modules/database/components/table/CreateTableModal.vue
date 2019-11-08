<template>
  <Modal>
    <h2 class="box-title">Create new table</h2>
    <div v-if="error" class="alert alert-error alert-has-icon">
      <div class="alert-icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert-title">{{ errorTitle }}</div>
      <p class="alert-content">{{ errorMessage }}</p>
    </div>
    <TableForm ref="tableForm" @submitted="submitted">
      <div class="actions">
        <div class="align-right">
          <button
            class="button button-large"
            :class="{ 'button-loading': loading }"
            :disabled="loading"
          >
            Add table
          </button>
        </div>
      </div>
    </TableForm>
  </Modal>
</template>

<script>
import TableForm from './TableForm'

import modal from '@/mixins/modal'

export default {
  name: 'CreateTableModal',
  components: { TableForm },
  mixins: [modal],
  props: {
    application: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      error: false,
      errorTitle: '',
      errorMessage: ''
    }
  },
  methods: {
    submitted(values) {
      this.loading = true
      this.error = false

      this.$store
        .dispatch('table/create', { database: this.application, values })
        .then(() => {
          this.loading = false
          this.hide()
        })
        .catch(error => {
          this.loading = false

          if (error.handler) {
            const message = error.handler.getMessage('application')
            this.error = true
            this.errorTitle = message.title
            this.errorMessage = message.message
            error.handler.handled()
          } else {
            throw error
          }
        })
    }
  }
}
</script>
