<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-list'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.listRows') }}
      </h3>
      <p class="api-docs__content">
        To list rows in the {{ table.name }} table a
        <code class="api-docs__code">GET</code> request has to be made to the
        {{ table.name }} endpoint. The response is paginated and by default the
        first page is returned. The correct page can be fetched by providing the
        <code class="api-docs__code">page</code> and
        <code class="api-docs__code">size</code> query parameters.
      </p>
      <h4 class="api-docs__heading-4">Query parameters</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter
          name="page"
          :optional="true"
          type="integer"
          standard="1"
        >
          Defines which page of rows should be returned.
        </APIDocsParameter>
        <APIDocsParameter
          name="size"
          :optional="true"
          type="integer"
          standard="100"
        >
          Defines how many rows should be returned per page.
        </APIDocsParameter>
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
          <br />
          <br />
          Additionally when
          <code class="api-docs__code">user_field_names</code>
          is set then the behaviour of the other GET parameters
          <code class="api-docs__code">order_by</code>,
          <code class="api-docs__code">include</code> and
          <code class="api-docs__code">exclude</code> changes. They instead
          expect comma separated lists of the actual field names instead.
        </APIDocsParameter>
        <APIDocsParameter
          name="search"
          :optional="true"
          type="string"
          standard="''"
        >
          If provided only rows with data that matches the search query are
          going to be returned.
        </APIDocsParameter>
        <APIDocsParameter
          name="order_by"
          :optional="true"
          type="string"
          standard="'id'"
        >
          Optionally the rows can be ordered by fields separated by comma. By
          default or if prepended with a '+' a field is ordered in ascending
          (A-Z) order, but by prepending the field with a '-' it can be ordered
          descending (Z-A).
          <h4>
            With <code class="api-docs__code">user_field_names</code>
            :
          </h4>
          <code class="api-docs__code">order_by</code> should be a comma
          separated list of the field names to order by. For example if you
          provide the following GET parameter
          <code class="api-docs__code">order_by=My Field,-My Field 2</code>
          the rows will ordered by the field called
          <code class="api-docs__code">My Field</code>
          in ascending order. If some fields have the same value, that subset
          will be ordered by the field called
          <code class="api-docs__code">My Field 2</code> in descending order.
          <br />
          <br />
          Ensure fields with names starting with a
          <code class="api-docs__code">+</code> or
          <code class="api-docs__code">-</code> are explicitly prepended with
          another <code class="api-docs__code">+</code> or
          <code class="api-docs__code">-</code>. E.g
          <code class="api-docs__code">+-Name</code>.
          <br />
          <br />
          Field names containing commas should be surrounded by quotes:
          <code class="api-docs__code">"Name ,"</code>. Field names including
          quotes should be escaped using a backslash:
          <code class="api-docs__code">Name \"</code>.
          <h4>
            Without <code class="api-docs__code">user_field_names</code>
            :
          </h4>
          <code class="api-docs__code">order_by</code> should be a comma
          separated list of <code class="api-docs__code">field_</code> followed
          by the id of the field to order by. For example if you provide the
          following GET parameter
          <code class="api-docs__code">order_by=field_1,-field_2</code>
          the rows will ordered by
          <code class="api-docs__code">field_1</code>
          in ascending order. If some fields have the same value, that subset
          will be ordered by
          <code class="api-docs__code">field_2</code> in descending order.
        </APIDocsParameter>
        <APIDocsParameter
          name="filter__{field}__{filter}"
          :optional="true"
          type="string"
        >
          The rows can optionally be filtered by the same view filters available
          for the views. Multiple filters can be provided if they follow the
          same format. The
          <code class="api-docs__code">field</code> and
          <code class="api-docs__code">filter</code> variable indicate how to
          filter and the value indicates where to filter on. <br /><br />
          For example if you provide the following GET parameter
          <code class="api-docs__code">filter__field_1__equal=test</code>
          then only rows where the value of field_1 is equal to test are going
          to be returned.
          <a @click.prevent="navigate('section-filters')">
            A list of all filters can be found here.</a
          >
        </APIDocsParameter>
        <APIDocsParameter
          name="filter_type"
          :optional="true"
          type="string"
          standard="'AND'"
        >
          <code class="api-docs__code">AND</code>: Indicates that the rows must
          match all the provided filters.
          <br />
          <code class="api-docs__code">OR</code>: Indicates that the rows only
          have to match one of the filters. <br /><br />
          This works only if two or more filters are provided.
        </APIDocsParameter>
        <APIDocsParameter name="include" :optional="true" type="string">
          All the fields are included in the response by default. You can select
          a subset of fields to include by providing the include query
          parameter.
          <h4>
            With <code class="api-docs__code">user_field_names</code>
            :
          </h4>
          <code class="api-docs__code">include</code> should be a comma
          separated list of field names to be included in results. For example
          if you provide the following GET param:
          <code class="api-docs__code">include=My Field,-My Field 2</code>
          then only those fields will be included (unless they are explicitly
          excluded).
          <br />
          <br />
          Field names containing commas should be surrounded by quotes:
          <code class="api-docs__code">"Name ,"</code>. Field names including
          quotes should be escaped using a backslash:
          <code class="api-docs__code">Name \"</code>.
          <h4>Without <code class="api-docs__code">user_field_names</code>:</h4>
          <code class="api-docs__code">include</code> should be a comma
          separated list of <code class="api-docs__code">field_</code> followed
          by the id of the field to include in the results. For example: If you
          provide the following GET parameter
          <code class="api-docs__code">exclude=field_1,field_2</code>
          then the fields with id
          <code class="api-docs__code">1</code> and id
          <code class="api-docs__code">2</code>
          then only those fields will be included (unless they are explicitly
          excluded).
        </APIDocsParameter>
        <APIDocsParameter name="exclude" :optional="true" type="string">
          All the fields are included in the response by default. You can select
          a subset of fields to exclude by providing the exclude query
          parameter.
          <h4>
            With <code class="api-docs__code">user_field_names</code>
            :
          </h4>
          <code class="api-docs__code">exclude</code> should be a comma
          separated list of field names to be excluded from the results. For
          example if you provide the following GET param:
          <code class="api-docs__code">exclude=My Field,-My Field 2</code>
          then those fields will be excluded.
          <br />
          <br />
          Field names containing commas should be surrounded by quotes:
          <code class="api-docs__code">"Name ,"</code>. Field names including
          quotes should be escaped using a backslash:
          <code class="api-docs__code">Name \"</code>.
          <h4>Without <code class="api-docs__code">user_field_names</code>:</h4>
          <code class="api-docs__code">exclude</code> should be a comma
          separated list of <code class="api-docs__code">field_</code> followed
          by the id of the field to exclude from the results. For example: If
          you provide the following GET parameter
          <code class="api-docs__code">exclude=field_1,field_2</code>
          then the fields with id
          <code class="api-docs__code">1</code> and id
          <code class="api-docs__code">2</code> will be excluded.
        </APIDocsParameter>
      </ul>
    </div>
    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="GET"
        :url="getListUrl(table, true)"
        :response="{
          count: 1024,
          next: getListUrl(table, false) + '?page=2',
          previous: null,
          results: [getResponseItem(table)],
        }"
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
  name: 'APIDocsTableListRows',
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
    getListUrl: { type: Function, required: true },
    getResponseItem: { type: Function, required: true },
    getFieldMapping: { type: Function, required: true },
  },
  methods: {},
}
</script>

<i18n>
{
  "en": {
    "apiDocsTableListRows":{
    }
  },
  "fr": {
  }
}
</i18n>
