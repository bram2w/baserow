<template>
  <Context
    class="data-source-context"
    :class="{ 'context--loading-overlay': state === 'loading' }"
    @shown="shown"
  >
    <template v-if="state === 'loaded'">
      <div v-if="dataSources.length > 0">
        <DataSourceForm
          v-for="dataSource in dataSources"
          :ref="`dataSourceForm_${dataSource.id}`"
          :key="dataSource.id"
          :builder="builder"
          :default-values="dataSource"
          :integrations="integrations"
          @delete="deleteDataSource(dataSource)"
          @values-changed="updateDataSource(dataSource, $event)"
        />
      </div>

      <template v-else>
        <div class="data-source-context__none">
          <div class="data-source-context__none-title">
            {{ $t('dataSourceContext.noDataSourceTitle') }}
          </div>
          <div class="data-source-context__none-description">
            {{ $t('dataSourceContext.noDataSourceMessage') }}
          </div>
        </div>
      </template>

      <Button type="link" prepend-icon="plus" @click="createDataSource()">
        {{ $t('dataSourceContext.addDataSource') }}
      </Button>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import DataSourceForm from '@baserow/modules/builder/components/dataSource/DataSourceForm'
import { mapActions, mapGetters } from 'vuex'
import _ from 'lodash'
import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'DataSourceContext',
  components: { DataSourceForm },
  mixins: [context],
  inject: ['builder'],
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  data() {
    return { state: null }
  },
  computed: {
    ...mapGetters({
      integrations: 'integration/getIntegrations',
      dataSources: 'dataSource/getDataSources',
    }),
  },
  methods: {
    ...mapActions({
      actionFetchIntegrations: 'integration/fetch',
      actionFetchDataSources: 'dataSource/fetch',
      actionCreateDataSource: 'dataSource/create',
      actionUpdateDataSource: 'dataSource/debouncedUpdate',
      actionDeleteDataSource: 'dataSource/delete',
    }),
    async shown() {
      this.state = 'loading'
      try {
        await this.actionFetchDataSources({ page: this.page })
        await this.actionFetchIntegrations({ applicationId: this.builder.id })
      } catch (error) {
        notifyIf(error)
      }
      this.state = 'loaded'
    },
    async createDataSource() {
      try {
        await this.actionCreateDataSource({
          pageId: this.page.id,
          values: {},
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    async updateDataSource(dataSource, newValues) {
      const hasDifference = Object.entries(newValues).some(
        ([key, value]) => !_.isEqual(value, dataSource[key])
      )

      if (hasDifference) {
        try {
          await this.actionUpdateDataSource({
            dataSourceId: dataSource.id,
            values: clone(newValues),
          })
        } catch (error) {
          // Restore the previous saved values from the store
          this.$refs[`dataSourceForm_${dataSource.id}`][0].reset()
          notifyIf(error)
        }
      }
    },
    async deleteDataSource(dataSource) {
      try {
        await this.actionDeleteDataSource({ dataSourceId: dataSource.id })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
