<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-update'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.updateRow') }}
      </h3>
      <p class="api-docs__content">
        {{ $t('apiDocsTableUpdateRow.description', table) }}
      </p>
      <h4 class="api-docs__heading-4">{{ $t('apiDocs.pathParameters') }}</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="row_id" type="integer">
          {{ $t('apiDocsTableUpdateRow.rowId') }}
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
        <APIDocsParameter :optional="true" name="before" type="integer">
          {{ $t('apiDocsTableUpdateRow.before') }}
        </APIDocsParameter>
      </ul>
      <h4 class="api-docs__heading-4">{{ $t('apiDocs.requestBodySchema') }}</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter
          v-for="field in withoutReadOnly[table.id]"
          :key="field.id"
          :name="'field_' + field.id"
          :visible-name="field.name"
          :optional="true"
          :type="field._.type"
          :user-field-names="userFieldNames"
        >
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div v-html="field._.description"></div>
        </APIDocsParameter>
      </ul>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="PATCH"
        :url="getItemUrl(table, true)"
        :request="getRequestExample(table)"
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
  name: 'APIDocsTableUpdateRow',
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
    withoutReadOnly: { type: Object, required: true },
    userFieldNames: { type: Boolean, required: true },
    getItemUrl: { type: Function, required: true },
    getRequestExample: { type: Function, required: true },
    getResponseItem: { type: Function, required: true },
    getFieldMapping: { type: Function, required: true },
  },
  methods: {},
}
</script>
