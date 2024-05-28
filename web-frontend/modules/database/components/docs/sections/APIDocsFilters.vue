<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h2 id="section-filters" class="api-docs__heading-2">
        {{ $t('apiDocs.filters') }}
      </h2>
      <table class="api-docs__table">
        <thead>
          <tr>
            <th>{{ $t('apiDocsFilters.filter') }}</th>
            <th>{{ $t('apiDocsFilters.exampleValue') }}</th>
            <th>{{ $t('apiDocsFilters.example') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="filter in viewFilterTypes" :key="filter.type">
            <td>
              {{ filter.type }}
              <Badge
                v-if="filter.isDeprecated()"
                color="yellow"
                class="margin-left-1"
                >{{ $t('apiDocsFilters.deprecated') }}</Badge
              >
            </td>
            <td>{{ filter.example }}</td>
            <td>
              {{ $t('apiDocsFilters.field', { name: filter.getName() }) }}
              <template v-if="filter.example !== ''"
                >'{{ filter.example }}'</template
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'APIDocsFilters',
  props: {},
  computed: {
    viewFilterTypes() {
      return Object.values(this.$registry.getAll('viewFilter'))
    },
  },
}
</script>
