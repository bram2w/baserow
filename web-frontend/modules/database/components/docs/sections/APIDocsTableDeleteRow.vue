<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-delete'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.deleteRow') }}
      </h3>
      <p class="api-docs__content">
        {{ $t('apiDocsTableDeleteRow.description', table) }}
      </p>
      <h4 class="api-docs__heading-4">{{ $t('apiDocs.pathParameters') }}</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="row_id" type="integer">
          {{ $t('apiDocsTableDeleteRow.rowId') }}
        </APIDocsParameter>
      </ul>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="DELETE"
        :url="getItemUrl(table, false)"
        :include-user-fields-checkbox="false"
        @input="$emit('input', $event)"
      ></APIDocsExample>
    </div>
  </div>
</template>

<script>
import APIDocsExample from '@baserow/modules/database/components/docs/APIDocsExample'
import APIDocsParameter from '@baserow/modules/database/components/docs/APIDocsParameter'

export default {
  name: 'APIDocsTableDeleteRow',
  components: {
    APIDocsParameter,
    APIDocsExample,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    table: { type: Object, required: true },
    getItemUrl: { type: Function, required: true },
  },
}
</script>

<i18n>
{
  "en": {
    "apiDocsTableDeleteRow":{
      "description": "Deletes an existing {name} row.",
      "rowId": "The unique identifier of the row that needs to be deleted."
    }
  },
  "fr": {
    "apiDocsTableDeleteRow":{
      "description": "Supprime une ligne de la table *{name}*.",
      "rowId": "L'identifiant unique de la ligne à supprimer."
    }
  }
}
</i18n>
