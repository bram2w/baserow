<template>
  <Modal>
    <h2 class="box__title">Create new {{ viewType.getName() | lowercase }}</h2>
    <Error :error="error"></Error>
    <component
      :is="viewType.getViewFormComponent()"
      ref="viewForm"
      @submitted="submitted"
    >
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            Add {{ viewType.getName() | lowercase }}
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
  name: 'CreateViewModal',
  mixins: [modal, error],
  props: {
    table: {
      type: Object,
      required: true,
    },
    viewType: {
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
        await this.$store.dispatch('view/create', {
          type: this.viewType.type,
          table: this.table,
          values,
        })
        this.loading = false
        this.$emit('created')
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'view')
      }
    },
  },
}
</script>
