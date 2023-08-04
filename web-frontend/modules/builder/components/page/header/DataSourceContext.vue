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

      <Button
        type="link"
        prepend-icon="plus"
        :loading="creationInProgress"
        @click="createDataSource()"
      >
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
    return { state: null, creationInProgress: false }
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
      actionCreateDataSource: 'dataSource/create',
      actionUpdateDataSource: 'dataSource/debouncedUpdate',
      actionDeleteDataSource: 'dataSource/delete',
    }),
    async shown() {
      this.state = 'loading'
      try {
        await this.actionFetchIntegrations({ applicationId: this.builder.id })
      } catch (error) {
        notifyIf(error)
      }
      this.state = 'loaded'
    },
    async createDataSource() {
      this.creationInProgress = true
      try {
        await this.actionCreateDataSource({
          pageId: this.page.id,
          values: {},
        })
      } catch (error) {
        notifyIf(error)
      }
      this.creationInProgress = false
    },
    async updateDataSource(dataSource, newValues) {
      const differences = Object.fromEntries(
        Object.entries(newValues).filter(
          ([key, value]) => !_.isEqual(value, dataSource[key])
        )
      )

      if (Object.keys(differences).length > 0) {
        try {
          await this.actionUpdateDataSource({
            dataSourceId: dataSource.id,
            values: clone(differences),
          })
          if (differences.type) {
            this.$refs[`dataSourceForm_${dataSource.id}`][0].reset()
          }
        } catch (error) {
          // Restore the previously saved values from the store
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
