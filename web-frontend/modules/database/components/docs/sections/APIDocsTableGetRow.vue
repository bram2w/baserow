<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-get'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.getRow') }}
      </h3>
      <p class="api-docs__content">Fetch a single {{ table.name }} row.</p>
      <h4 class="api-docs__heading-4">Path parameters</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="row_id" type="integer">
          The unique identifier of the row that is requested.
        </APIDocsParameter>
      </ul>
      <h4 class="api-docs__heading-4">Query parameters</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="user_field_names" :optional="true" type="any">
          When any value is provided for the
          <code class="api-docs__code">user_field_names</code> GET param then
          field names returned by this endpoint will be the actual names of the
          fields. <br />
          <br />
          If the
          <code class="api-docs__code">user_field_names</code> GET param is not
          provided, then all returned field names will be
          <code class="api-docs__code">field_</code> followed by the id of the
          field. For example <code class="api-docs__code">field_1</code> refers
          to the field with an id of <code class="api-docs__code">1</code>.
        </APIDocsParameter>
      </ul>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="GET"
        :url="getItemUrl(table, true)"
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
  name: 'APIDocsTableGetRow',
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
  methods: {},
}
</script>

<i18n>
{
  "en": {
    "APIDocsTableGetRow":{
    }
  },
  "fr": {
  }
}
</i18n>
