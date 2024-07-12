<template>
  <FormulaInputGroup
    v-bind="$attrs"
    small-label
    required
    :data-explorer-loading="dataExplorerLoading"
    :data-providers="dataProviders"
    :application-context="
      applicationContext ?? {
        page,
        builder,
        mode,
        ...applicationContextAdditions,
      }
    "
    :small="small"
    v-on="$listeners"
  >
    <template #after-input>
      <slot name="after-input"></slot>
    </template>
  </FormulaInputGroup>
</template>

<script>
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import { DataSourceDataProviderType } from '@baserow/modules/builder/dataProviderTypes'

export default {
  name: 'ApplicationBuilderFormulaInputGroup',
  components: { FormulaInputGroup },
  inject: {
    page: {
      from: 'page',
    },
    builder: {
      from: 'builder',
    },
    mode: {
      from: 'mode',
    },
    applicationContext: {
      from: 'applicationContext',
      default: null,
    },
  },
  props: {
    dataProvidersAllowed: {
      type: Array,
      required: false,
      default: () => [],
    },
    applicationContextAdditions: {
      type: Object,
      required: false,
      default: () => {},
    },
    small: {
      type: Boolean,
      required: false,
      default: true,
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
      return this.dataProvidersAllowed.map((dataProviderName) =>
        this.$registry.get('builderDataProvider', dataProviderName)
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
        [DataSourceDataProviderType.getType()]:
          this.dataSourceLoading || this.dataSourceContentLoading,
      }
    },
  },
}
</script>
