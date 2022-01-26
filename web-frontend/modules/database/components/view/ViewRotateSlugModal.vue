<template>
  <Modal>
    <h2 class="box__title">{{ $t('viewRotateSlugModal.title') }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        {{
          $t('viewRotateSlugModal.refreshWarning', {
            viewName: view.name,
            viewTypeSharingLinkName,
          })
        }}
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--primary"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="rotateSlug()"
          >
            {{ $t('viewRotateSlugModal.generateNewURL') }}
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import ViewService from '@baserow/modules/database/services/view'

export default {
  name: 'ViewRotateSlugModal',
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
  computed: {
    viewTypeSharingLinkName() {
      return this.$registry.get('view', this.view.type).getSharingLinkName()
    },
  },
  methods: {
    async rotateSlug() {
      this.hideError()
      this.loading = true

      try {
        const { data } = await ViewService(this.$client).rotateSlug(
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
