<template>
  <Modal>
    <h2 class="box-title">Create new {{ viewType.name | lowercase }}</h2>
    <div v-if="error" class="alert alert-error alert-has-icon">
      <div class="alert-icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert-title">{{ errorTitle }}</div>
      <p class="alert-content">{{ errorMessage }}</p>
    </div>
    <component
      :is="viewType.getViewFormComponent()"
      ref="viewForm"
      @submitted="submitted"
    >
      <div class="actions">
        <div class="align-right">
          <button
            class="button button-large"
            :class="{ 'button-loading': loading }"
            :disabled="loading"
          >
            Add {{ viewType.name | lowercase }}
          </button>
        </div>
      </div>
    </component>
  </Modal>
</template>

<script>
import modal from '@/mixins/modal'

export default {
  name: 'CreateViewModal',
  mixins: [modal],
  props: {
    table: {
      type: Object,
      required: true
    },
    viewType: {
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
        .dispatch('view/create', {
          type: this.viewType.type,
          table: this.table,
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
