<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h2 id="section-errors" class="api-docs__heading-2">
        {{ $t('apiDocs.errors') }}
      </h2>
      <table class="api-docs__table">
        <thead>
          <tr>
            <th>{{ $t('apiDocsErrors.errorCode') }}</th>
            <th>{{ $t('apiDocsErrors.name') }}</th>
            <th>{{ $t('apiDocsErrors.description') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>200</td>
            <td>Ok</td>
            <td>
              {{ $t('apiDocsErrors.okDescription') }}
            </td>
          </tr>
          <tr>
            <td>400</td>
            <td>Bad request</td>
            <td>
              {{ $t('apiDocsErrors.badRequestDescription') }}
            </td>
          </tr>
          <tr>
            <td>401</td>
            <td>Unauthorized</td>
            <td>
              {{ $t('apiDocsErrors.unauthorizedDescription') }}
            </td>
          </tr>
          <tr>
            <td>404</td>
            <td>Not found</td>
            <td>
              {{ $t('apiDocsErrors.notFoundDescription') }}
            </td>
          </tr>
          <tr>
            <td>413</td>
            <td>Request Entity Too Large</td>
            <td>
              {{ $t('apiDocsErrors.requestEntityTooLargeDescription') }}
            </td>
          </tr>
          <tr>
            <td>500</td>
            <td>Internal Server Error</td>
            <td>
              {{ $t('apiDocsErrors.internalErrorDescription') }}
            </td>
          </tr>
          <tr>
            <td>502</td>
            <td>Bad gateway</td>
            <td>
              {{ $t('apiDocsErrors.badGatewayDescription') }}
            </td>
          </tr>
          <tr>
            <td>503</td>
            <td>Service unavailable</td>
            <td>
              {{ $t('apiDocsErrors.unavailableDescription') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        :url="$env.PUBLIC_BACKEND_URL"
        type=""
        :response="{
          error: 'ERROR_NO_PERMISSION_TO_TABLE',
          description: 'The token does not have permissions to the table.',
        }"
        @input="$emit('input', $event)"
      ></APIDocsExample>
    </div>
  </div>
</template>

<script>
import APIDocsExample from '@baserow/modules/database/components/docs/APIDocsExample'

export default {
  name: 'APIDocsErrors',
  components: {
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
    "apiDocsErrors":{
      "errorCode": "Error code",
      "name": "Name",
      "description": "Description",
      "okDescription": "Request completed successfully.",
      "badRequestDescription": "The request contains invalid values or the JSON could not be parsed.",
      "unauthorizedDescription": "When you try to access an endpoint without valid token.",
      "notFoundDescription": "Row or table is not found.",
      "requestEntityTooLargeDescription": "The request exceeded the maximum allowed payload size.",
      "internalErrorDescription": "The server encountered an unexpected condition.",
      "badGatewayDescription": "Baserow is restarting or an unexpected outage is in progress.",
      "unavailableDescription": "The server could not process your request in time."
    }
  },
  "fr": {
    "apiDocsErrors":{
      "errorCode": "Code",
      "name": "Nom",
      "description": "Description",
      "okDescription": "La requête a été executée avec succès.",
      "badRequestDescription": "La requête contient des valeurs invalides ou le contenu JSON n'a pas pu être décodé.",
      "unauthorizedDescription": "Le jeton d'authentification utilisé est invalide.",
      "notFoundDescription": "La ligne ou la table n'a pas été trouvée.",
      "requestEntityTooLargeDescription": "La taille du contenu de la requête dépasse la taille maximale autorisée.",
      "internalErrorDescription": "Le serveur a rencontré une erreur interne inatendue.",
      "badGatewayDescription": "Baserow est en cours de démarrage ou une interruption du service est en cours.",
      "unavailableDescription": "Le serveur n'a pas répondu dans les délais impartis."
    }
  }
}
</i18n>
