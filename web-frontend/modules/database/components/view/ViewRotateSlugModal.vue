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

<i18n>
{
  "en": {
    "viewRotateSlugModal": {
      "title": "Refresh URL",
      "refreshWarning": "Are you sure that you want to refresh the URL of {viewName}? After refreshing, a new URL will be generated and it will not be possible to access the {viewTypeSharingLinkName} via the old URL. Everyone that you have shared the URL with, won't be able to access the {viewTypeSharingLinkName}.",
      "generateNewURL": "Generate new URL"

    }
  },
  "fr": {
    "viewRotateSlugModal": {
      "title": "Mettre à jour le lien",
      "refreshWarning": "Êtes-vous sûr·e de vouloir mettre à jour le lien vers {viewTypeSharingLinkName} {viewName} ? Après la mise à jour, il ne sera plus possible de consulter {viewTypeSharingLinkName} via l'ancien lien. Les personnes possédant le lien ne seront plus en mesure d'accéder à la page affichant {viewTypeSharingLinkName}.",
      "generateNewURL": "Générer une nouvelle URL"
    }
  }
}
</i18n>
