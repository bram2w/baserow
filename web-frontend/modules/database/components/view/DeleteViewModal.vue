<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('deleteViewModal.title', { name: view.name }) }}
    </h2>
    <Error :error="error"></Error>
    <div>
      <i18n path="deleteViewModal.description" tag="p">
        <template #name>
          <strong>{{ view.name }}</strong>
        </template>
      </i18n>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="deleteView()"
          >
            {{ $t('deleteViewModal.delete') }}
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'DeleteViewModal',
  mixins: [modal, error],
  props: {
    view: {
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
    async deleteView() {
      this.hideError()
      this.loading = true

      try {
        await this.$store.dispatch('view/delete', this.view)
        this.hide()
      } catch (error) {
        this.handleError(error, 'view')
      }

      this.loading = false
    },
  },
}
</script>
