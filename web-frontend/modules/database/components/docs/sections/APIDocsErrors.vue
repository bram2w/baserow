<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h2 id="section-errors" class="api-docs__heading-2">
        {{ $t('apiDocs.errors') }}
      </h2>
      <table class="api-docs__table">
        <thead>
          <tr>
            <th>Error code</th>
            <th>Name</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>200</td>
            <td>Ok</td>
            <td>Request completed successfully.</td>
          </tr>
          <tr>
            <td>400</td>
            <td>Bad request</td>
            <td>
              The request contains invalid values of the JSON could not be
              parsed.
            </td>
          </tr>
          <tr>
            <td>401</td>
            <td>Unauthorized</td>
            <td>When you try to access an endpoint without valid token.</td>
          </tr>
          <tr>
            <td>404</td>
            <td>Not found</td>
            <td>Row or table is not found.</td>
          </tr>
          <tr>
            <td>413</td>
            <td>Request Entity Too Large</td>
            <td>The request exceeded the maximum allowed payload size.</td>
          </tr>
          <tr>
            <td>500</td>
            <td>Internal Server Error</td>
            <td>The server encountered an unexpected condition.</td>
          </tr>
          <tr>
            <td>502</td>
            <td>Bad gateway</td>
            <td>
              Baserow is restarting or an unexpected outage is in progress.
            </td>
          </tr>
          <tr>
            <td>503</td>
            <td>Service unavailable</td>
            <td>The server could not process your request in time.</td>
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
    }
  },
  "fr": {
  }
}
</i18n>
