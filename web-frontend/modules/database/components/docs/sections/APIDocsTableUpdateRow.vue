<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-update'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.updateRow') }}
      </h3>
      <p class="api-docs__content">Updates an existing {{ table.name }} row.</p>
      <h4 class="api-docs__heading-4">Path parameters</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="row_id" type="integer">
          The unique identifier of the row that needs to be updated.
        </APIDocsParameter>
      </ul>
      <h4 class="api-docs__heading-4">Query parameters</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="user_field_names" :optional="true" type="any">
          When any value is provided for the
          <code class="api-docs__code">user_field_names</code> GET param then
          field names expected and returned by this endpoint will be the actual
          field names. <br />
          <br />
          If the
          <code class="api-docs__code">user_field_names</code> GET param is not
          provided, then field names expected and returned will be
          <code class="api-docs__code">field_</code> followed by the id of the
          field. For example <code class="api-docs__code">field_1</code> refers
          to the field with an id of <code class="api-docs__code">1</code>.
        </APIDocsParameter>
        <APIDocsParameter :optional="true" name="before" type="integer">
          If provided then the newly created row will be positioned before the
          row with the provided id.
        </APIDocsParameter>
      </ul>
      <h4 class="api-docs__heading-4">Request body schema</h4>
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

<i18n>
{
  "en": {
    "APIDocsTableUpdateRow":{
    }
  },
  "fr": {
  }
}
</i18n>
