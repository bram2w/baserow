<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('action.createNew') }} {{ applicationType.getName() | lowercase }}
    </h2>
    <Error :error="error"></Error>
    <component
      :is="applicationType.getApplicationFormComponent()"
      ref="applicationForm"
      @submitted="submitted"
    >
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('action.add') }} {{ applicationType.getName() | lowercase }}
          </button>
        </div>
      </div>
    </component>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'CreateApplicationModal',
  mixins: [modal, error],
  props: {
    applicationType: {
      type: Object,
      required: true,
    },
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
    async submitted(values) {
      this.loading = true
      this.hideError()

      try {
        await this.$store.dispatch('application/create', {
          type: this.applicationType.type,
          group: this.group,
          values,
        })
        this.loading = false
        this.$emit('created')
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'application')
      }
    },
  },
}
</script>
