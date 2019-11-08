<template>
  <Modal>
    <h2 class="box-title">Create new {{ application.name | lowercase }}</h2>
    <div v-if="error" class="alert alert-error alert-has-icon">
      <div class="alert-icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert-title">{{ errorTitle }}</div>
      <p class="alert-content">{{ errorMessage }}</p>
    </div>
    <component
      :is="application.getApplicationFormComponent()"
      ref="applicationForm"
      @submitted="submitted"
    >
      <div class="actions">
        <div class="align-right">
          <button
            class="button button-large"
            :class="{ 'button-loading': loading }"
            :disabled="loading"
          >
            Add {{ application.name | lowercase }}
          </button>
        </div>
      </div>
    </component>
  </Modal>
</template>

<script>
import modal from '@/mixins/modal'

export default {
  name: 'CreateApplicationModal',
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
        .dispatch('application/create', {
          type: this.application.type,
          values: values
        })
        .then(() => {
          this.loading = false
          this.$emit('created')
          this.hide()
        })
        .catch(error => {
          this.loading = false

          if (error.handler) {
            const message = error.handler.getMessage('group')
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
