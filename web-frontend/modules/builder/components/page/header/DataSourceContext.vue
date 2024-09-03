<template>
  <Context
    :class="{ 'context--loading-overlay': state === 'loading' }"
    max-height-if-outside-viewport
    @shown="shown"
  >
    <div class="data-source-context__container">
      <div
        v-if="state === 'loaded'"
        v-auto-overflow-scroll
        class="data-source-context__content data-source-context__content--scrollable"
      >
        <div v-if="dataSources.length > 0" class="data-source-context__forms">
          <ReadOnlyForm
            v-for="dataSource in dataSources"
            :key="dataSource.id"
            :read-only="
              !$hasPermission(
                'builder.page.data_source.update',
                dataSource,
                workspace.id
              )
            "
          >
            <DataSourceForm
              :id="dataSource.id"
              :ref="`dataSourceForm_${dataSource.id}`"
              :builder="builder"
              :data-source="dataSource"
              :page="page"
              :default-values="dataSource"
              :integrations="integrations"
              :loading="dataSourcesLoading.includes(dataSource.id)"
              @delete="deleteDataSource(dataSource)"
              @values-changed="updateDataSource(dataSource, $event)"
            />
          </ReadOnlyForm>
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
      </div>
      <div class="context__footer">
        <ButtonText
          v-if="
            $hasPermission(
              'builder.page.create_data_source',
              page,
              workspace.id
            )
          "
          icon="iconoir-plus"
          :loading="creationInProgress"
          @click="createDataSource()"
        >
          {{ $t('dataSourceContext.addDataSource') }}
        </ButtonText>
      </div>
    </div>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import DataSourceForm from '@baserow/modules/builder/components/dataSource/DataSourceForm'
import { mapActions } from 'vuex'
import _ from 'lodash'
import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'DataSourceContext',
  components: { DataSourceForm },
  mixins: [context],
  inject: ['workspace', 'builder'],
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      state: 'loaded',
      creationInProgress: false,
      onGoingUpdate: {},
      dataSourcesLoading: [],
    }
  },
  computed: {
    integrations() {
      return this.$store.getters['integration/getIntegrations'](this.builder)
    },
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
      clearElementContent: 'elementContent/clearElementContent',
    }),
    async shown() {
      try {
        await Promise.all([
          this.actionFetchIntegrations({
            application: this.builder,
          }),
        ])
      } catch (error) {
        notifyIf(error)
      }
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
