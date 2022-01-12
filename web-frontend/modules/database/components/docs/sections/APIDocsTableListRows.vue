<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h3
        :id="'section-table-' + table.id + '-list'"
        class="api-docs__heading-3"
      >
        {{ $t('apiDocs.listRows') }}
      </h3>
      <MarkdownIt
        class="api-docs__content"
        :content="$t('apiDocsTableListRows.description', table)"
      />
      <h4 class="api-docs__heading-4">
        {{ $t('apiDocs.queryParameters') }}
      </h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter
          name="page"
          :optional="true"
          type="integer"
          standard="1"
        >
          {{ $t('apiDocsTableListRows.page') }}
        </APIDocsParameter>
        <APIDocsParameter
          name="size"
          :optional="true"
          type="integer"
          standard="100"
        >
          {{ $t('apiDocsTableListRows.size') }}
        </APIDocsParameter>
        <APIDocsParameter name="user_field_names" :optional="true" type="any">
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocsTableListRows.userFieldNames')"
          />
        </APIDocsParameter>
        <APIDocsParameter
          name="search"
          :optional="true"
          type="string"
          standard="''"
        >
          {{ $t('apiDocsTableListRows.search') }}
        </APIDocsParameter>
        <APIDocsParameter
          name="order_by"
          :optional="true"
          type="string"
          standard="'id'"
        >
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocsTableListRows.orderBy')"
          />
        </APIDocsParameter>
        <APIDocsParameter
          name="filter__{field}__{filter}"
          :optional="true"
          type="string"
        >
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocsTableListRows.filter', table)"
          />
          <a @click.prevent="navigate('section-filters')">
            {{ $t('apiDocsTableListRows.filterLink') }}</a
          >
        </APIDocsParameter>
        <APIDocsParameter
          name="filter_type"
          :optional="true"
          type="string"
          standard="'AND'"
        >
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocsTableListRows.filterType')"
          />
        </APIDocsParameter>
        <APIDocsParameter name="include" :optional="true" type="string">
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocsTableListRows.include')"
          />
        </APIDocsParameter>
        <APIDocsParameter name="exclude" :optional="true" type="string">
          <MarkdownIt
            class="api-docs__content"
            :content="$t('apiDocsTableListRows.exclude')"
          />
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
    navigate: { type: Function, required: true },
    getResponseItem: { type: Function, required: true },
    getFieldMapping: { type: Function, required: true },
  },
  methods: {},
}
</script>

<i18n>
{
  "en": {
    "apiDocsTableListRows": {
      "description": "To list rows in the *{name}* table a `GET` request has to be made to the *{name}* endpoint. The response is paginated and by default the first page is returned. The correct page can be fetched by providing the `page` and `size` query parameters.",
      "page": "Defines which page of rows should be returned.",
      "size": "Defines how many rows should be returned per page.",
      "userFieldNames": "When any value is provided for the `user_field_names` GET param then field names returned by this endpoint will be the actual names of the fields.\n\n If the `user_field_names` GET param is not provided, then all returned field names will be `field_` followed by the id of the field. For example `field_1` refers to the field with an id of `1`.\n\n Additionally when `user_field_names` is set then the behaviour of the other GET parameters `order_by`, `include` and `exclude` changes. They instead expect comma separated lists of the actual field names instead.",
      "search": "If provided only rows with data that matches the search query are going to be returned.",
      "orderBy": "Optionally the rows can be ordered by fields separated by comma. By default or if prepended with a '+' a field is ordered in ascending (A-Z) order, but by prepending the field with a '-' it can be ordered descending (Z-A).\n\n #### With `user_field_names`:\n\n `order_by` should be a comma separated list of the field names to order by. For example if you provide the following GET parameter `order_by=My Field,-My Field 2` the rows will ordered by the field called `My Field` in ascending order. If some fields have the same value, that subset will be ordered by the field called `My Field 2` in descending order.\n\n Ensure fields with names starting with a `+` or `-` are explicitly prepended with another `+` or `-`. E.g `+-Name`.\n\n Le nom des champs contenant des virgules doit être entouré par des guillements : `\"Nom ,\"`. Si le nom des champs contient des guillements, ils doivent alors être protégés en utilisant le charactère `\\`. Ex : `Nom \\\"`.\n\n#### Without `user_field_names`:\n\n `order_by` should be a comma separated list of `field_` followed by the id of the field to order by. For example if you provide the following GET parameter `order_by=field_1,-field_2` the rows will ordered by `field_1` in ascending order. If some fields have the same value, that subset will be ordered by `field_2` in descending order.",
      "filter": "The rows can optionally be filtered by the same view filters available for the views. Multiple filters can be provided if they follow the same format. The `field` and `filter` variable indicate how to filter and the value indicates where to filter on.\n\n For example if you provide the following GET parameter `filter__field_1__equal=test` then only rows where the value of field_1 is equal to test are going to be returned.",
      "filterLink": "A list of all filters can be found here.",
      "filterType": "- `AND`: Indicates that the rows must match all the provided filters.\n- `OR`: Indicates that the rows only have to match one of the filters.\n\n This works only if two or more filters are provided.",
      "include": "All the fields are included in the response by default. You can select a subset of fields to include by providing the include query parameter.\n\n #### With `user_field_names`:\n\n `include` should be a comma separated list of field names to be included in results. For example if you provide the following GET param: `include=My Field,-My Field 2` then only those fields will be included (unless they are explicitly excluded).\n\n Le nom des champs contenant des virgules doit être entouré par des guillements : `\"Nom ,\"`. Si le nom des champs contient des guillements, ils doivent alors être protégés en utilisant le charactère `\\`. Ex : `Nom \\\"`.\n\n #### Without `user_field_names`:\n\n `include` should be a comma separated list of `field_` followed by the id of the field to include in the results. For example: If you provide the following GET parameter `exclude=field_1,field_2` then the fields with id `1` and id `2` then only those fields will be included (unless they are explicitly excluded).",
      "exclude": "All the fields are included in the response by default. You can select a subset of fields to exclude by providing the exclude query parameter.\n\n #### With `user_field_names`:\n\n `exclude` should be a comma separated list of field names to be excluded from the results. For example if you provide the following GET param: `exclude=My Field,-My Field 2` then those fields will be excluded.\n\n Le nom des champs contenant des virgules doit être entouré par des guillements : `\"Nom ,\"`. Si le nom des champs contient des guillements, ils doivent alors être protégés en utilisant le charactère `\\`. Ex : `Nom \\\"`.\n\n #### Without `user_field_names`:\n\n `exclude` should be a comma separated list of `field_` followed by the id of the field to exclude from the results. For example: If you provide the following GET parameter `exclude=field_1,field_2` then the fields with id `1` and id `2` will be excluded."
    }
  },
  "fr": {
    "apiDocsTableListRows": {
      "description": "Afin de lister les lignes de la table *{name}* une requête de type `GET` doit être envoyée au point d'accès de la table *{name}*. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.",
      "page": "Permet de choisir la page.",
      "size": "Permet de définir le nombre de ligne par page.",
      "userFieldNames": "Quand une valeur est fournie pour le paramètre GET `user_field_names`, les noms des champs du résultat seront ceux définis par l'utilisateur.\n\n Si le paramêtre `user_field_names` n'est pas défini, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.\n\n De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.",
      "search": "Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.",
      "orderBy": "Ce paramèter permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).\n\n #### Avec `user_field_names` :\n\n `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.\n\n Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.\n\n Le nom des champs contenant des virgules doit être entouré par des guillements : `\"Nom ,\"`. Si le nom des champs contient des guillements, ceux-ci doivent alors être protégés en utilisant le charactère `\\`. Ex : `Nom \\\"`.\n\n #### Sans `user_field_names` :\n\n `order_by` doit être une liste de `field_` suivi par l'identifiant du champ a ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.",
      "filter": "Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles dans les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.\n\n Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à *test* seront retournées.",
      "filterLink": "Une liste des filtres disponibles peut être consultée ici.",
      "filterType": "- `AND` : indique que les lignes doivent satisfaire tous les filtres définis.\n- `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.\n\n Cela fonctionne uniquement quand au moins 2 filtres sont définis.",
      "include": "Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.\n\n #### Avec `user_field_names` :\n\n `include` doit être une liste des noms définis par l'utilisateur des champs que l'on souhaite conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).\n\n Le nom des champs contenant des virgules doit être entouré par des guillements : `\"Nom ,\"`. Si le nom des champs contient des guillements, ceux-ci doivent alors être protégés en utilisant le charactère `\\`. Ex : `Nom \\\"`.\n\n #### Sans `user_field_names` :\n\n `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `exclude=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).",
      "exclude": "Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.\n\n #### Avec `user_field_names`:\n\n `exclude` doit être une liste des noms définis par l'utilisateur des champs que l'on souhaite exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.\n\n Le nom des champs contenant des virgules doit être entouré par des guillements : `\"Nom ,\"`. Si le nom des champs contient des guillements, ceux-ci doivent alors être protégés en utilisant le charactère `\\`. Ex : `Nom \\\"`.\n\n #### Sans `user_field_names`:\n\n `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par example, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus."
    }
  }
}
</i18n>
