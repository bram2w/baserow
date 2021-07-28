<template>
  <div class="api-docs">
    <div ref="header" class="api-docs__header">
      <nuxt-link :to="{ name: 'index' }" class="api-docs__logo">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
      <a
        ref="databasesToggle"
        class="api-docs__switch"
        @click.prevent="databasesOpen = !databasesOpen"
      >
        <i class="api-docs__switch-icon fas fa-database"></i>
        {{ database.name }} database API documentation
      </a>
      <div class="api-docs__open">
        <nuxt-link
          v-if="database.tables.length > 0"
          :to="{
            name: 'database-table',
            params: {
              databaseId: database.id,
              tableId: database.tables[0].id,
            },
          }"
          class="button button--ghost"
          >open database</nuxt-link
        >
      </div>
    </div>
    <div v-show="databasesOpen" ref="databases" class="api-docs__databases">
      <div class="api-docs__databases-inner">
        <APIDocsSelectDatabase :selected="database.id"></APIDocsSelectDatabase>
      </div>
    </div>
    <div class="api-docs__nav">
      <ul class="api-docs__nav-list">
        <li>
          <a
            class="api-docs__nav-link"
            :class="{ active: navActive === 'section-introduction' }"
            @click.prevent="navigate('section-introduction')"
            >Introduction</a
          >
        </li>
        <li>
          <a
            class="api-docs__nav-link"
            :class="{ active: navActive === 'section-authentication' }"
            @click.prevent="navigate('section-authentication')"
            >Authentication</a
          >
        </li>
        <li v-for="table in database.tables" :key="table.id">
          <a
            class="api-docs__nav-link"
            :class="{ active: navActive === 'section-table-' + table.id }"
            @click.prevent="navigate('section-table-' + table.id)"
            >{{ table.name }} table <small>(id: {{ table.id }})</small></a
          >
          <ul
            class="api-docs__nav-sub"
            :class="{
              open:
                navActive === 'section-table-' + table.id ||
                navActive === 'section-table-' + table.id + '-fields' ||
                navActive === 'section-table-' + table.id + '-field-list' ||
                navActive === 'section-table-' + table.id + '-list' ||
                navActive === 'section-table-' + table.id + '-get' ||
                navActive === 'section-table-' + table.id + '-create' ||
                navActive === 'section-table-' + table.id + '-update' ||
                navActive === 'section-table-' + table.id + '-move' ||
                navActive === 'section-table-' + table.id + '-delete',
            }"
          >
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-fields',
                }"
                @click.prevent="
                  navigate('section-table-' + table.id + '-fields')
                "
                >Fields</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active:
                    navActive === 'section-table-' + table.id + '-field-list',
                }"
                @click.prevent="
                  navigate('section-table-' + table.id + '-field-list')
                "
                >List fields</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-list',
                }"
                @click.prevent="navigate('section-table-' + table.id + '-list')"
                >List rows</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-get',
                }"
                @click.prevent="navigate('section-table-' + table.id + '-get')"
                >Get row</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-create',
                }"
                @click.prevent="
                  navigate('section-table-' + table.id + '-create')
                "
                >Create row</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-update',
                }"
                @click.prevent="
                  navigate('section-table-' + table.id + '-update')
                "
                >Update row</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-move',
                }"
                @click.prevent="navigate('section-table-' + table.id + '-move')"
                >Move row</a
              >
            </li>
            <li>
              <a
                class="api-docs__nav-link"
                :class="{
                  active: navActive === 'section-table-' + table.id + '-delete',
                }"
                @click.prevent="
                  navigate('section-table-' + table.id + '-delete')
                "
                >Delete row</a
              >
            </li>
          </ul>
        </li>
        <li>
          <a
            class="api-docs__nav-link"
            :class="{ active: navActive === 'section-filters' }"
            @click.prevent="navigate('section-filters')"
            >Filters</a
          >
        </li>
        <li>
          <a
            class="api-docs__nav-link"
            :class="{ active: navActive === 'section-errors' }"
            @click.prevent="navigate('section-errors')"
            >Errors</a
          >
        </li>
      </ul>
    </div>
    <div class="api-docs__body">
      <div class="api-docs__item">
        <div class="api-docs__left">
          <h2 id="section-introduction" class="api-docs__heading-2">
            Introduction
          </h2>
          <p class="api-docs__content">
            The {{ database.name }} database provides an easy way to integrate
            the data with any external system. The API follows REST semantics,
            uses JSON to encode objects and relies on standard HTTP codes,
            machine and human readable errors to signal operation outcomes.
          </p>
          <p class="api-docs__content">
            This documentation is generated automatically based the tables and
            fields that are in your database. If you make changes to your
            database, table or fields it could be that the API interface has
            also changed. Therefore, make sure that you update your API
            implementation accordingly.
          </p>
          <p class="api-docs__content">
            The ID of this database is:
            <code class="api-docs__code">{{ database.id }}</code>
            <br />
            Javascript example API client:
            <a href="https://github.com/axios/axios" target="_blank">axios</a>
            <br />
            Python example API client:
            <a href="https://requests.readthedocs.io/en/master/" target="_blank"
              >requests</a
            >
          </p>
        </div>
      </div>
      <div class="api-docs__item">
        <div class="api-docs__left">
          <h2 id="section-authentication" class="api-docs__heading-2">
            Authentication
          </h2>
          <p class="api-docs__content">
            Baserow uses a simple token based authentication. You need to
            generate at least one API token in your
            <a @click.prevent="$refs.settingsModal.show('tokens')">settings</a>
            to use the endpoints described below. It is possible to give create,
            read, update and delete permissions up until table level per token.
            You can authenticate to the API by providing your API token in the
            HTTP authorization bearer token header. All API requests must be
            authenticated and made over HTTPS.
          </p>
        </div>
        <div class="api-docs__right">
          <APIDocsExample
            v-model="exampleData"
            :url="$env.PUBLIC_BACKEND_URL"
            :include-user-fields-checkbox="false"
            type=""
          ></APIDocsExample>
        </div>
      </div>
      <div v-for="table in database.tables" :key="table.id">
        <div class="item">
          <div class="api-docs__left">
            <h2 :id="'section-table-' + table.id">{{ table.name }} table</h2>
            <p class="api-docs__content">
              The ID of this table is:
              <code class="api-docs__code">{{ table.id }}</code>
            </p>
            <h3
              :id="'section-table-' + table.id + '-fields'"
              class="api-docs__heading-3"
            >
              Fields
            </h3>
            <p class="api-docs__content">
              Each row in the {{ table.name }} table contains the following
              fields.
            </p>
            <table class="api-docs__table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Compatible filters</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="field in fields[table.id]">
                  <tr
                    :key="field.id + '-1'"
                    class="api-docs__table-without-border"
                  >
                    <td>field_{{ field.id }}</td>
                    <td>{{ field.name }}</td>
                    <td>
                      <code class="api-docs__code margin-bottom-1">
                        {{ field._.type }}
                      </code>
                    </td>
                    <td>
                      <code
                        v-for="filter in getCompatibleFilterTypes(field.type)"
                        :key="filter.type"
                        class="
                          api-docs__code
                          api-docs__code--small
                          api-docs__code--clickable
                          margin-bottom-1 margin-right-1
                        "
                        @click.prevent="navigate('section-filters')"
                        >{{ filter.type }}</code
                      >
                    </td>
                  </tr>
                  <tr :key="field.id + '-2'">
                    <td colspan="4">
                      <div
                        class="api-docs__table-content"
                        v-html="field._.description"
                      ></div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-field-list'"
              class="api-docs__heading-3"
            >
              List fields
            </h3>
            <p class="api-docs__content">
              To list fields of the {{ table.name }} table a
              <code class="api-docs__code">GET</code> request has to be made to
              the {{ table.name }} fields endpoint. It's only possible to list
              the fields if the token has read, create or update permissions.
            </p>
            <h4 class="api-docs__heading-4">Result field properties</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter name="id" :optional="false" type="integer">
                Field primary key. Can be used to generate the database column
                name by adding
                <code class="api-docs__code">field_</code> prefix.
              </APIDocsParameter>
              <APIDocsParameter name="name" :optional="false" type="string">
                Field name.
              </APIDocsParameter>
              <APIDocsParameter
                name="table_id"
                :optional="false"
                type="integer"
              >
                Related table id.
              </APIDocsParameter>
              <APIDocsParameter name="order" :optional="false" type="integer">
                Field order in table. 0 for the first field.
              </APIDocsParameter>
              <APIDocsParameter name="primary" :optional="false" type="boolean">
                Indicates if the field is a primary field. If
                <code class="api-docs__code">true</code> the field cannot be
                deleted and the value should represent the whole row.
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
              v-model="exampleData"
              type="GET"
              :url="getFieldsURL(table)"
              :response="getResponseFields(table)"
              :include-user-fields-checkbox="false"
            ></APIDocsExample>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-list'"
              class="api-docs__heading-3"
            >
              List rows
            </h3>
            <p class="api-docs__content">
              To list rows in the {{ table.name }} table a
              <code class="api-docs__code">GET</code> request has to be made to
              the {{ table.name }} endpoint. The response is paginated and by
              default the first page is returned. The correct page can be
              fetched by providing the
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
              <APIDocsParameter
                name="user_field_names"
                :optional="true"
                type="any"
              >
                When any value is provided for the
                <code class="api-docs__code">user_field_names</code> GET param
                then field names returned by this endpoint will be the actual
                names of the fields. <br />
                <br />
                If the
                <code class="api-docs__code">user_field_names</code> GET param
                is not provided, then all returned field names will be
                <code class="api-docs__code">field_</code> followed by the id of
                the field. For example
                <code class="api-docs__code">field_1</code> refers to the field
                with an id of <code class="api-docs__code">1</code>. <br />
                <br />
                Additionally when
                <code class="api-docs__code">user_field_names</code>
                is set then the behaviour of the other GET parameters
                <code class="api-docs__code">order_by</code>,
                <code class="api-docs__code">include</code> and
                <code class="api-docs__code">exclude</code> changes. They
                instead expect comma separated lists of the actual field names
                instead.
              </APIDocsParameter>
              <APIDocsParameter
                name="search"
                :optional="true"
                type="string"
                standard="''"
              >
                If provided only rows with data that matches the search query
                are going to be returned.
              </APIDocsParameter>
              <APIDocsParameter
                name="order_by"
                :optional="true"
                type="string"
                standard="'id'"
              >
                Optionally the rows can be ordered by fields separated by comma.
                By default or if prepended with a '+' a field is ordered in
                ascending (A-Z) order, but by prepending the field with a '-' it
                can be ordered descending (Z-A).
                <h4>
                  With <code class="api-docs__code">user_field_names</code>
                  :
                </h4>
                <code class="api-docs__code">order_by</code> should be a comma
                separated list of the field names to order by. For example if
                you provide the following GET parameter
                <code class="api-docs__code"
                  >order_by=My Field,-My Field 2</code
                >
                the rows will ordered by the field called
                <code class="api-docs__code">My Field</code>
                in ascending order. If some fields have the same value, that
                subset will be ordered by the field called
                <code class="api-docs__code">My Field 2</code> in descending
                order.
                <br />
                <br />
                Ensure fields with names starting with a
                <code class="api-docs__code">+</code> or
                <code class="api-docs__code">-</code> are explicitly prepended
                with another <code class="api-docs__code">+</code> or
                <code class="api-docs__code">-</code>. E.g
                <code class="api-docs__code">+-Name</code>.
                <br />
                <br />
                Field names containing commas should be surrounded by quotes:
                <code class="api-docs__code">"Name ,"</code>. Field names
                including quotes should be escaped using a backslash:
                <code class="api-docs__code">Name \"</code>.
                <h4>
                  Without <code class="api-docs__code">user_field_names</code>
                  :
                </h4>
                <code class="api-docs__code">order_by</code> should be a comma
                separated list of
                <code class="api-docs__code">field_</code> followed by the id of
                the field to order by. For example if you provide the following
                GET parameter
                <code class="api-docs__code">order_by=field_1,-field_2</code>
                the rows will ordered by
                <code class="api-docs__code">field_1</code>
                in ascending order. If some fields have the same value, that
                subset will be ordered by
                <code class="api-docs__code">field_2</code> in descending order.
              </APIDocsParameter>
              <APIDocsParameter
                name="filter__{field}__{filter}"
                :optional="true"
                type="string"
              >
                The rows can optionally be filtered by the same view filters
                available for the views. Multiple filters can be provided if
                they follow the same format. The
                <code class="api-docs__code">field</code> and
                <code class="api-docs__code">filter</code> variable indicate how
                to filter and the value indicates where to filter on.
                <br /><br />
                For example if you provide the following GET parameter
                <code class="api-docs__code">filter__field_1__equal=test</code>
                then only rows where the value of field_1 is equal to test are
                going to be returned.
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
                <code class="api-docs__code">AND</code>: Indicates that the rows
                must match all the provided filters.
                <br />
                <code class="api-docs__code">OR</code>: Indicates that the rows
                only have to match one of the filters. <br /><br />
                This works only if two or more filters are provided.
              </APIDocsParameter>
              <APIDocsParameter name="include" :optional="true" type="string">
                All the fields are included in the response by default. You can
                select a subset of fields to include by providing the include
                query parameter.
                <h4>
                  With <code class="api-docs__code">user_field_names</code>
                  :
                </h4>
                <code class="api-docs__code">include</code> should be a comma
                separated list of field names to be included in results. For
                example if you provide the following GET param:
                <code class="api-docs__code">include=My Field,-My Field 2</code>
                then only those fields will be included (unless they are
                explicitly excluded).
                <br />
                <br />
                Field names containing commas should be surrounded by quotes:
                <code class="api-docs__code">"Name ,"</code>. Field names
                including quotes should be escaped using a backslash:
                <code class="api-docs__code">Name \"</code>.
                <h4>
                  Without <code class="api-docs__code">user_field_names</code>:
                </h4>
                <code class="api-docs__code">include</code> should be a comma
                separated list of
                <code class="api-docs__code">field_</code> followed by the id of
                the field to include in the results. For example: If you provide
                the following GET parameter
                <code class="api-docs__code">exclude=field_1,field_2</code>
                then the fields with id
                <code class="api-docs__code">1</code> and id
                <code class="api-docs__code">2</code>
                then only those fields will be included (unless they are
                explicitly excluded).
              </APIDocsParameter>
              <APIDocsParameter name="exclude" :optional="true" type="string">
                All the fields are included in the response by default. You can
                select a subset of fields to exclude by providing the exclude
                query parameter.
                <h4>
                  With <code class="api-docs__code">user_field_names</code>
                  :
                </h4>
                <code class="api-docs__code">exclude</code> should be a comma
                separated list of field names to be excluded from the results.
                For example if you provide the following GET param:
                <code class="api-docs__code">exclude=My Field,-My Field 2</code>
                then those fields will be excluded.
                <br />
                <br />
                Field names containing commas should be surrounded by quotes:
                <code class="api-docs__code">"Name ,"</code>. Field names
                including quotes should be escaped using a backslash:
                <code class="api-docs__code">Name \"</code>.
                <h4>
                  Without <code class="api-docs__code">user_field_names</code>:
                </h4>
                <code class="api-docs__code">exclude</code> should be a comma
                separated list of
                <code class="api-docs__code">field_</code> followed by the id of
                the field to exclude from the results. For example: If you
                provide the following GET parameter
                <code class="api-docs__code">exclude=field_1,field_2</code>
                then the fields with id
                <code class="api-docs__code">1</code> and id
                <code class="api-docs__code">2</code> will be excluded.
              </APIDocsParameter>
            </ul>
          </div>
          <div class="api-docs__right">
            <APIDocsExample
              v-model="exampleData"
              type="GET"
              :url="getListURL(table, true)"
              :response="{
                count: 1024,
                next: getListURL(table, false) + '?page=2',
                previous: null,
                results: [getResponseItem(table)],
              }"
              :mapping="getFieldMapping(table)"
            ></APIDocsExample>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-get'"
              class="api-docs__heading-3"
            >
              Get row
            </h3>
            <p class="api-docs__content">
              Fetch a single {{ table.name }} row.
            </p>
            <h4 class="api-docs__heading-4">Path parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter name="row_id" type="integer">
                The unique identifier of the row that is requested.
              </APIDocsParameter>
            </ul>
            <h4 class="api-docs__heading-4">Query parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter
                name="user_field_names"
                :optional="true"
                type="any"
              >
                When any value is provided for the
                <code class="api-docs__code">user_field_names</code> GET param
                then field names returned by this endpoint will be the actual
                names of the fields. <br />
                <br />
                If the
                <code class="api-docs__code">user_field_names</code> GET param
                is not provided, then all returned field names will be
                <code class="api-docs__code">field_</code> followed by the id of
                the field. For example
                <code class="api-docs__code">field_1</code> refers to the field
                with an id of <code class="api-docs__code">1</code>.
              </APIDocsParameter>
            </ul>
          </div>
          <div class="api-docs__right">
            <APIDocsExample
              v-model="exampleData"
              type="GET"
              :url="getItemURL(table, true)"
              :response="getResponseItem(table)"
              :mapping="getFieldMapping(table)"
            ></APIDocsExample>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-create'"
              class="api-docs__heading-3"
            >
              Create row
            </h3>
            <p class="api-docs__content">Create a new {{ table.name }} row.</p>
            <h4 class="api-docs__heading-4">Query parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter
                name="user_field_names"
                :optional="true"
                type="any"
              >
                When any value is provided for the
                <code class="api-docs__code">user_field_names</code> GET param
                then field names expected and returned by this endpoint will be
                the actual field names. <br />
                <br />
                If the
                <code class="api-docs__code">user_field_names</code> GET param
                is not provided, then field names expected and returned will be
                <code class="api-docs__code">field_</code> followed by the id of
                the field. For example
                <code class="api-docs__code">field_1</code> refers to the field
                with an id of <code class="api-docs__code">1</code>.
              </APIDocsParameter>
              <APIDocsParameter :optional="true" name="before" type="integer">
                If provided then the newly created row will be positioned before
                the row with the provided id.
              </APIDocsParameter>
            </ul>
            <h4 class="api-docs__heading-4">Request body schema</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter
                v-for="field in fields[table.id]"
                :key="field.id"
                :name="'field_' + field.id"
                :visible-name="field.name"
                :optional="true"
                :type="field._.type"
                :user-field-names="exampleData.userFieldNames"
              >
                <div v-html="field._.description"></div>
              </APIDocsParameter>
            </ul>
          </div>
          <div class="api-docs__right">
            <APIDocsExample
              v-model="exampleData"
              type="POST"
              :url="getListURL(table, true)"
              :request="getRequestExample(table)"
              :response="getResponseItem(table)"
              :mapping="getFieldMapping(table)"
            ></APIDocsExample>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-update'"
              class="api-docs__heading-3"
            >
              Update row
            </h3>
            <p class="api-docs__content">
              Updates an existing {{ table.name }} row.
            </p>
            <h4 class="api-docs__heading-4">Path parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter name="row_id" type="integer">
                The unique identifier of the row that needs to be updated.
              </APIDocsParameter>
            </ul>
            <h4 class="api-docs__heading-4">Query parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter
                name="user_field_names"
                :optional="true"
                type="any"
              >
                When any value is provided for the
                <code class="api-docs__code">user_field_names</code> GET param
                then field names expected and returned by this endpoint will be
                the actual field names. <br />
                <br />
                If the
                <code class="api-docs__code">user_field_names</code> GET param
                is not provided, then field names expected and returned will be
                <code class="api-docs__code">field_</code> followed by the id of
                the field. For example
                <code class="api-docs__code">field_1</code> refers to the field
                with an id of <code class="api-docs__code">1</code>.
              </APIDocsParameter>
              <APIDocsParameter :optional="true" name="before" type="integer">
                If provided then the newly created row will be positioned before
                the row with the provided id.
              </APIDocsParameter>
            </ul>
            <h4 class="api-docs__heading-4">Request body schema</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter
                v-for="field in fields[table.id]"
                :key="field.id"
                :name="'field_' + field.id"
                :visible-name="field.name"
                :optional="true"
                :type="field._.type"
                :user-field-names="exampleData.userFieldNames"
              >
                <div v-html="field._.description"></div>
              </APIDocsParameter>
            </ul>
          </div>
          <div class="api-docs__right">
            <APIDocsExample
              v-model="exampleData"
              type="PATCH"
              :url="getItemURL(table, true)"
              :request="getRequestExample(table)"
              :response="getResponseItem(table)"
              :mapping="getFieldMapping(table)"
            ></APIDocsExample>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-move'"
              class="api-docs__heading-3"
            >
              Move row
            </h3>
            <p class="api-docs__content">
              Moves an existing {{ table.name }} row before another row. If no
              `before_id` is provided, then the row will be moved to the end of
              the table.
            </p>
            <h4 class="api-docs__heading-4">Path parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter name="row_id" type="integer">
                Moves the row related to the value.
              </APIDocsParameter>
            </ul>
            <h4 class="api-docs__heading-4">Query parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter
                name="user_field_names"
                :optional="true"
                type="any"
              >
                When any value is provided for the
                <code class="api-docs__code">user_field_names</code> GET param
                then field names returned by this endpoint will be the actual
                names of the fields. <br />
                <br />
                If the
                <code class="api-docs__code">user_field_names</code> GET param
                is not provided, then all returned field names will be
                <code class="api-docs__code">field_</code> followed by the id of
                the field. For example
                <code class="api-docs__code">field_1</code> refers to the field
                with an id of <code class="api-docs__code">1</code>.
              </APIDocsParameter>
              <APIDocsParameter
                name="before_id"
                type="integer"
                :optional="true"
              >
                Moves the row related to the given `row_id` before the row
                related to the provided value. If not provided, then the row
                will be moved to the end.
              </APIDocsParameter>
            </ul>
          </div>
          <div class="api-docs__right">
            <APIDocsExample
              v-model="exampleData"
              type="PATCH"
              :url="getItemURL(table, false) + 'move/' + userFieldNamesParam"
              :response="getResponseItem(table)"
              :mapping="getFieldMapping(table)"
            ></APIDocsExample>
          </div>
        </div>
        <div class="api-docs__item">
          <div class="api-docs__left">
            <h3
              :id="'section-table-' + table.id + '-delete'"
              class="api-docs__heading-3"
            >
              Delete row
            </h3>
            <p class="api-docs__content">
              Deletes an existing {{ table.name }} row.
            </p>
            <h4 class="api-docs__heading-4">Path parameters</h4>
            <ul class="api-docs__parameters">
              <APIDocsParameter name="row_id" type="integer">
                The unique identifier of the row that needs to be deleted.
              </APIDocsParameter>
            </ul>
          </div>
          <div class="api-docs__right">
            <APIDocsExample
              v-model="exampleData"
              type="DELETE"
              :url="getItemURL(table, false)"
              :include-user-fields-checkbox="false"
            ></APIDocsExample>
          </div>
        </div>
      </div>
      <div class="api-docs__item">
        <div class="api-docs__left">
          <h2 id="section-filters" class="api-docs__heading-2">Filters</h2>
          <table class="api-docs__table">
            <thead>
              <tr>
                <th>Filter</th>
                <th>Example value</th>
                <th>Full example</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="filter in viewFilterTypes" :key="filter.type">
                <td>{{ filter.type }}</td>
                <td>{{ filter.example }}</td>
                <td>
                  field {{ filter.name }}
                  <template v-if="filter.example !== ''"
                    >'{{ filter.example }}'</template
                  >
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="api-docs__item">
        <div class="api-docs__left">
          <h2 id="section-errors" class="api-docs__heading-2">HTTP Errors</h2>
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
            v-model="exampleData"
            :url="$env.PUBLIC_BACKEND_URL"
            type=""
            :response="{
              error: 'ERROR_NO_PERMISSION_TO_TABLE',
              description: 'he token does not have permissions to the table.',
            }"
          ></APIDocsExample>
        </div>
      </div>
    </div>
    <SettingsModal ref="settingsModal"></SettingsModal>
  </div>
</template>

<script>
import { isElement } from '@baserow/modules/core/utils/dom'
import SettingsModal from '@baserow/modules/core/components/settings/SettingsModal'
import APIDocsExample from '@baserow/modules/database/components/docs/APIDocsExample'
import APIDocsParameter from '@baserow/modules/database/components/docs/APIDocsParameter'
import APIDocsSelectDatabase from '@baserow/modules/database/components/docs/APIDocsSelectDatabase'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import FieldService from '@baserow/modules/database/services/field'

export default {
  name: 'APIDocsDatabase',
  components: {
    SettingsModal,
    APIDocsExample,
    APIDocsParameter,
    APIDocsSelectDatabase,
  },
  middleware: ['authenticated', 'groupsAndApplications'],
  async asyncData({ store, params, error, app }) {
    const databaseId = parseInt(params.databaseId)
    const database = store.getters['application/get'](databaseId)
    const type = DatabaseApplicationType.getType()

    if (database === undefined || database.type !== type) {
      return error({ statusCode: 404, message: 'Database not found.' })
    }

    const fields = {}
    const populateField = (field) => {
      const fieldType = app.$registry.get('field', field.type)
      field._ = {
        type: fieldType.getDocsDataType(field),
        description: fieldType.getDocsDescription(field),
        requestExample: fieldType.getDocsRequestExample(field),
        responseExample: fieldType.getDocsResponseExample(field),
        fieldResponseExample: fieldType.getDocsFieldResponseExample(field),
      }
      return field
    }

    for (const i in database.tables) {
      const table = database.tables[i]
      const { data } = await FieldService(app.$client).fetchAll(table.id)
      fields[table.id] = data.map((field) => populateField(field))
    }

    return { database, fields }
  },
  data() {
    return {
      exampleData: {
        // Indicates which request example type is shown.
        type: 'curl',
        userFieldNames: true,
      },
      // Indicates which navigation item is active.
      navActive: '',
      // Indicates if the databases sidebar is open.
      databasesOpen: false,
    }
  },
  head() {
    return {
      title: `API Documentation ${this.database.name}`,
    }
  },
  computed: {
    userFieldNamesParam() {
      return this.exampleData.userFieldNames ? '?user_field_names=true' : ''
    },
    viewFilterTypes() {
      return Object.values(this.$registry.getAll('viewFilter'))
    },
  },
  mounted() {
    // When the user clicks outside the databases sidebar and it is open then it must
    // be closed.
    this.$el.clickOutsideEvent = (event) => {
      if (
        this.databasesOpen &&
        !isElement(this.$refs.databasesToggle, event.target) &&
        !isElement(this.$refs.databases, event.target)
      ) {
        this.databasesOpen = false
      }
    }
    document.body.addEventListener('click', this.$el.clickOutsideEvent)

    // When the user scrolls in the body or when the window is resized, the active
    // navigation item must be updated.
    this.$el.scrollEvent = () => this.updateNav()
    this.$el.resizeEvent = () => this.updateNav()
    window.addEventListener('scroll', this.$el.scrollEvent)
    window.addEventListener('resize', this.$el.resizeEvent)
    this.updateNav()
  },
  beforeDestroy() {
    document.body.removeEventListener('click', this.$el.clickOutsideEvent)
    window.removeEventListener('scroll', this.$el.scrollEvent)
    window.removeEventListener('resize', this.$el.resizeEvent)
  },
  methods: {
    /**
     * Called when the user scrolls or when the window is resized. It will check which
     * navigation item is active based on the scroll position of the available ids.
     */
    updateNav() {
      const body = document.documentElement
      const sections = body.querySelectorAll('[id]')
      sections.forEach((section, index) => {
        const top = section.offsetTop
        const nextIndex = (index + 1).toString()
        const next =
          nextIndex in sections
            ? sections[nextIndex].offsetTop
            : body.scrollHeight
        if (top <= body.scrollTop && body.scrollTop < next) {
          this.navActive = section.id
        }
      })
    },
    navigate(to) {
      const section = document.querySelector(`[id='${to}']`)
      document.documentElement.scrollTop =
        section.offsetTop - 20 + this.$refs.header.clientHeight
    },
    /**
     * Generates an example request object based on the available fields of the table.
     */
    getRequestExample(table, response = false) {
      const item = {}
      this.fields[table.id].forEach((field) => {
        const example = response
          ? field._.responseExample
          : field._.requestExample
        if (this.exampleData.userFieldNames) {
          item[field.name] = example
        } else {
          item[`field_${field.id}`] = example
        }
      })
      return item
    },
    /**
     * Generates an example response object based on the available fields of the table.
     */
    getResponseItem(table) {
      const item = { id: 0, order: '1.00000000000000000000' }
      Object.assign(item, this.getRequestExample(table, true))
      return item
    },
    /**
     * Generates a sample field list response based on the available fields of the table.
     */
    getResponseFields(table) {
      return this.fields[table.id]
        .slice(0, 3)
        .map(({ _: { fieldResponseExample } }) => fieldResponseExample)
    },
    /**
     * Returns the mapping of the field id as key and the field name as value.
     */
    getFieldMapping(table) {
      const mapping = {}
      this.fields[table.id].forEach((field) => {
        if (this.exampleData.userFieldNames) {
          mapping[field.name] = `field_${field.id}`
        } else {
          mapping[`field_${field.id}`] = field.name
        }
      })
      return mapping
    },
    getFieldsURL(table) {
      return `${this.$env.PUBLIC_BACKEND_URL}/api/database/fields/table/${table.id}/`
    },
    getListURL(table, addUserFieldParam) {
      return `${this.$env.PUBLIC_BACKEND_URL}/api/database/rows/table/${
        table.id
      }/${addUserFieldParam ? this.userFieldNamesParam : ''}`
    },
    getItemURL(table, addUserFieldParam) {
      return (
        this.getListURL(table) +
        '{row_id}/' +
        (addUserFieldParam ? this.userFieldNamesParam : '')
      )
    },
    getCompatibleFilterTypes(fieldType) {
      return this.viewFilterTypes.filter((filter) =>
        filter.compatibleFieldTypes.includes(fieldType)
      )
    },
  },
}
</script>
