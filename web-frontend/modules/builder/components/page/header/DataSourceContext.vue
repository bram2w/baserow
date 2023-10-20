<template>
  <Context
    class="data-source-context"
    :class="{ 'context--loading-overlay': state === 'loading' }"
    :overflow-scroll="true"
    :max-height-if-outside-viewport="true"
    @shown="shown"
  >
    <template v-if="state === 'loaded'">
      <div v-if="dataSources.length > 0">
        <DataSourceForm
          v-for="dataSource in dataSources"
          :id="dataSource.id"
          :ref="`dataSourceForm_${dataSource.id}`"
          :key="dataSource.id"
          :builder="builder"
          :data-source="dataSource"
          :page="page"
          :default-values="dataSource"
          :integrations="integrations"
          :loading="dataSourcesLoading.includes(dataSource.id)"
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
        prepend-icon="baserow-icon-plus"
        size="tiny"
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
    return {
      state: null,
      creationInProgress: false,
      onGoingUpdate: {},
      dataSourcesLoading: [],
    }
  },
  computed: {
    ...mapGetters({
      integrations: 'integration/getIntegrations',
    }),
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
  },
  methods: {
    ...mapActions({
      actionFetchIntegrations: 'integration/fetch',
      actionCreateDataSource: 'dataSource/create',
      actionUpdateDataSource: 'dataSource/debouncedUpdate',
      actionDeleteDataSource: 'dataSource/delete',
      actionFetchDataSources: 'dataSource/fetch',
    }),
    async shown() {
      this.state = 'loading'
      try {
        await Promise.all([
          this.actionFetchIntegrations({
            applicationId: this.builder.id,
          }),
          this.actionFetchDataSources({ page: this.page }),
        ])
      } catch (error) {
        notifyIf(error)
      }
      this.state = 'loaded'
    },
    async createDataSource() {
      this.creationInProgress = true
      try {
        await this.actionCreateDataSource({
          page: this.page,
          values: {},
        })
      } catch (error) {
        notifyIf(error)
      }
      this.creationInProgress = false
    },
    async updateDataSource(dataSource, newValues) {
      // We only need to set the loading state if the integration is updated
      if (
        newValues.integration_id !== null &&
        newValues.integration_id !== undefined
      ) {
        this.dataSourcesLoading.push(dataSource.id)
      }

      const differences = Object.fromEntries(
        Object.entries(newValues).filter(
          ([key, value]) => !_.isEqual(value, dataSource[key])
        )
      )

      if (Object.keys(differences).length > 0) {
        try {
          await this.actionUpdateDataSource({
            page: this.page,
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

      this.dataSourcesLoading = this.dataSourcesLoading.filter(
        (id) => id !== dataSource.id
      )
    },
    async deleteDataSource(dataSource) {
      try {
        await this.actionDeleteDataSource({
          page: this.page,
          dataSourceId: dataSource.id,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
