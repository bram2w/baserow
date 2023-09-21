<template>
  <FormulaInputGroup
    v-bind="$attrs"
    :data-explorer-loading="dataExplorerLoading"
    :data-providers="dataProviders"
    v-on="$listeners"
  ></FormulaInputGroup>
</template>

<script>
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import { DataSourceDataProviderType } from '@baserow/modules/builder/dataProviderTypes'
export default {
  name: 'ApplicationBuilderFormulaInputGroup',
  components: { FormulaInputGroup },
  inject: ['page'],
  props: {
    dataProvidersAllowed: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  computed: {
    dataSourceLoading() {
      return this.$store.getters['dataSource/getLoading'](this.page)
    },
    dataSourceContentLoading() {
      return this.$store.getters['dataSourceContent/getLoading'](this.page)
    },
    dataProviders() {
      return Object.values(this.$registry.getAll('builderDataProvider')).filter(
        (dataProvider) =>
          this.dataProvidersAllowed.includes(dataProvider.getType())
      )
    },
    dataExplorerLoading() {
      return this.dataProvidersAllowed.some(
        (dataProviderName) => this.dataProviderLoadingMap[dataProviderName]
      )
    },
    /**
     * This mapping defines which data providers are affected by what loading states.
     * Since not all data providers are always used in every data explorer we
     * shouldn't put the data explorer in a loading state whenever some inaccessible
     * data is loading.
     */
    dataProviderLoadingMap() {
      return {
        [new DataSourceDataProviderType().getType()]:
          this.dataSourceLoading || this.dataSourceContentLoading,
      }
    },
  },
}
</script>
