<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h2 id="section-authentication" class="api-docs__heading-2">
        {{ $t('apiDocs.authent') }}
      </h2>
      <i18n path="apiDocsAuth.description" tag="p" class="api-docs__content">
        <template #settingsLink>
          <a @click.prevent="$refs.settingsModal.show('tokens')">{{
            $t('apiDocsAuth.settingsLink')
          }}</a>
        </template>
      </i18n>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        :url="$env.PUBLIC_BACKEND_URL"
        :include-user-fields-checkbox="false"
        type=""
        @input="$emit('input', $event)"
      ></APIDocsExample>
    </div>
    <SettingsModal ref="settingsModal"></SettingsModal>
  </div>
</template>

<script>
import SettingsModal from '@baserow/modules/core/components/settings/SettingsModal'
import APIDocsExample from '@baserow/modules/database/components/docs/APIDocsExample'

export default {
  name: 'APIDocsAuth',
  components: {
    SettingsModal,
    APIDocsExample,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
  },
}
</script>

<i18n>
{
  "en": {
    "apiDocsAuth":{
      "description": "Baserow uses a simple token based authentication. You need to generate at least one API token in your {settingsLink} to use the endpoints described below. It is possible to give create, read, update and delete permissions up until table level per token. You can authenticate to the API by providing your API token in the HTTP authorization bearer token header. All API requests must be authenticated and made over HTTPS.",
      "settingsLink": "settings"
    }
  },
  "fr": {
    "apiDocsAuth":{
      "description": "Baserow utilise un système d'authentification simple par jeton. Vous devez générer au moins un jeton d'API dans votre {settingsLink} afin d'utiliser les API suivantes. Il est possible de définir des droits de création, lecture, modification et suppression par table et ce pour chaque jeton. Pour vous authentifier à l'API, fournissez le jeton via l'entête HTTP «\u00A0Authorization\u00A0» de la requête. Tous les appels à l'API doivent être authentifiés et réalisés via le protocole sécurisé HTTPS.",
      "settingsLink": "compte"
    }
  }
}
</i18n>
