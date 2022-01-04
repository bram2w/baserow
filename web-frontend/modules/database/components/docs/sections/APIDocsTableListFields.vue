<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="`section-table-${table.id}-field-list`"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.listFields') }}
      </h3>
      <p class="api-docs__content">
        To list fields of the {{ table.name }} table a
        <code class="api-docs__code">GET</code> request has to be made to the
        {{ table.name }} fields endpoint. It's only possible to list the fields
        if the token has read, create or update permissions.
      </p>
      <h4 class="api-docs__heading-4">Result field properties</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="id" :optional="false" type="integer">
          Field primary key. Can be used to generate the database column name by
          adding
          <code class="api-docs__code">field_</code> prefix.
        </APIDocsParameter>
        <APIDocsParameter name="name" :optional="false" type="string">
          Field name.
        </APIDocsParameter>
        <APIDocsParameter name="table_id" :optional="false" type="integer">
          Related table id.
        </APIDocsParameter>
        <APIDocsParameter name="order" :optional="false" type="integer">
          Field order in table. 0 for the first field.
        </APIDocsParameter>
        <APIDocsParameter name="primary" :optional="false" type="boolean">
          Indicates if the field is a primary field. If
          <code class="api-docs__code">true</code> the field cannot be deleted
          and the value should represent the whole row.
        </APIDocsParameter>
        <APIDocsParameter name="type" :optional="false" type="string">
          Type defined for this field.
        </APIDocsParameter>
      </ul>
      <p class="api-docs__content">
        Some extra properties are not described here because they are type
        specific.
      </p>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="GET"
        :url="getFieldsURL(table)"
        :response="getResponseFields(table)"
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
  name: 'APIDocsTableListFields',
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
    fields: { type: Object, required: true },
  },
  methods: {
    getFieldsURL(table) {
      return `${this.$env.PUBLIC_BACKEND_URL}/api/database/fields/table/${table.id}/`
    },
    /**
     * Generates a sample field list response based on the available fields of the table.
     */
    getResponseFields(table) {
      return this.fields[table.id]
        .slice(0, 3)
        .map(({ _: { fieldResponseExample } }) => fieldResponseExample)
    },
  },
}
</script>

<i18n>
{
  "en": {
    "apiDocsTableListFields":{
    }
  },
  "fr": {
  }
}
</i18n>
