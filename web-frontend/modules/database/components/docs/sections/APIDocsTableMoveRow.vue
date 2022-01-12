<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-move'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.moveRow') }}
      </h3>
      <MarkdownIt
        class="api-docs__content"
        :content="$t('apiDocsTableMoveRow.description', table)"
      />
      <h4 class="api-docs__heading-4">{{ $t('apiDocs.pathParameters') }}</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="row_id" type="integer">
          {{ $t('apiDocsTableMoveRow.rowId') }}
        </APIDocsParameter>
      </ul>
      <h4 class="api-docs__heading-4">{{ $t('apiDocs.queryParameters') }}</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="user_field_names" :optional="true" type="any">
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocs.userFieldNamesDescription')"
          />
        </APIDocsParameter>
        <APIDocsParameter name="before_id" type="integer" :optional="true">
          {{ $t('apiDocsTableMoveRow.before') }}
        </APIDocsParameter>
      </ul>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="PATCH"
        :url="getItemUrl(table, false) + 'move/' + userFieldNamesParam"
        :response="getResponseItem(table)"
        :mapping="getFieldMapping(table)"
        @input="$emit('input', $event)"
      ></APIDocsExample>
    </div>
  </div>
</template>

<script>
import APIDocsExample from '@baserow/modules/database/components/docs/APIDocsExample'
import APIDocsParameter from '@baserow/modules/database/components/docs/APIDocsParameter'

export default {
  name: 'APIDocsTableMoveRow',
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
    getResponseItem: { type: Function, required: true },
    getFieldMapping: { type: Function, required: true },
  },
  computed: {
    userFieldNamesParam() {
      return this.userFieldNames ? '?user_field_names=true' : ''
    },
  },
  methods: {},
}
</script>

<i18n>
{
  "en": {
    "apiDocsTableMoveRow": {
      "description": "Moves an existing {name} row before another row. If no `before_id` is provided, then the row will be moved to the end of the table.",
      "rowId": "Moves the row related to the value.",
      "before": "Moves the row related to the given `row_id` before the row related to the provided value. If not provided, then the row will be moved to the end."
    }
  },
  "fr": {
    "apiDocsTableMoveRow": {
      "description": "Déplace une ligne existante de la table *{name}* avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.",
      "rowId": "Identifiant unique de la ligne à déplacer.",
      "before": "Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table."
    }
  }
}
</i18n>
