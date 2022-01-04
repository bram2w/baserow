<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-move'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.moveRow') }}
      </h3>
      <p class="api-docs__content">
        Moves an existing {{ table.name }} row before another row. If no
        `before_id` is provided, then the row will be moved to the end of the
        table.
      </p>
      <h4 class="api-docs__heading-4">Path parameters</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="row_id" type="integer">
          Moves the row related to the value.
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
        <APIDocsParameter name="before_id" type="integer" :optional="true">
          Moves the row related to the given `row_id` before the row related to
          the provided value. If not provided, then the row will be moved to the
          end.
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
    "APIDocsTableMoveRow":{
    }
  },
  "fr": {
  }
}
</i18n>
