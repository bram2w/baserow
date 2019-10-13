<template>
  <Modal>
    <h2 class="box-title">Create new {{ application.name | lowercase }}</h2>
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
      loading: false
    }
  },
  methods: {
    submitted(values) {
      this.loading = true
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
        .catch(() => {
          this.loading = false
        })
    }
  }
}
</script>
