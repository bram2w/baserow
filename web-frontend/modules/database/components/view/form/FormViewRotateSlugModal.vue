<template>
  <Modal>
    <h2 class="box__title">Refresh URL</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure that you want to refresh the URL of {{ view.name }}? After
        refreshing, a new URL will be generated and it will not be possible to
        access the form via the old URL. Everyone that you have shared the URL
        with, won't be able to access the form.
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--primary"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="rotateSlug()"
          >
            Generate new URL
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import formViewHelpers from '@baserow/modules/database/mixins/formViewHelpers'
import FormService from '@baserow/modules/database/services/view/form'

export default {
  name: 'FormViewRotateSlugModal',
  mixins: [modal, error, formViewHelpers],
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
    async rotateSlug() {
      this.hideError()
      this.loading = true

      try {
        const { data } = await FormService(this.$client).rotateSlug(
          this.view.id
        )
        await this.$store.dispatch('view/forceUpdate', {
          view: this.view,
          values: data,
        })
        this.hide()
      } catch (error) {
        this.handleError(error, 'table')
      }

      this.loading = false
    },
  },
}
</script>
