<template>
  <div class="audit-log__table">
    <AuditLogExportModal
      ref="exportModal"
      :filters="filters"
      :workspace-id="workspaceId"
    ></AuditLogExportModal>
    <CrudTable
      :columns="columns"
      :filters="filters"
      :default-column-sorts="[{ key: 'timestamp', direction: 'asc' }]"
      :service="service"
      :enable-search="false"
      row-id-key="id"
    >
      <template #title>
        {{
          workspaceId
            ? $t('auditLog.workspaceTitle', { workspaceName })
            : $t('auditLog.adminTitle')
        }}
      </template>
      <template #header-right-side>
        <Button
          type="primary"
          size="large"
          @click.prevent="$refs.exportModal.show()"
        >
          {{ $t('auditLog.exportToCsv') }}</Button
        >
      </template>
      <template #header-filters>
        <div
          class="audit-log__filters"
          :class="{ 'audit-log__filters--workspace': workspaceId }"
        >
          <FilterWrapper :name="$t('auditLog.filterUserTitle')">
            <PaginatedDropdown
              ref="userFilter"
              :value="filters.user_id"
              :fetch-page="fetchUsers"
              :empty-item-display-name="$t('auditLog.allUsers')"
              :not-selected-text="$t('auditLog.allUsers')"
              @input="filterUser"
            ></PaginatedDropdown>
          </FilterWrapper>
          <FilterWrapper
            v-if="!workspaceId"
            :name="$t('auditLog.filterWorkspaceTitle')"
          >
            <PaginatedDropdown
              ref="workspaceFilter"
              :value="filters.workspace_id"
              :fetch-page="fetchWorkspaces"
              :empty-item-display-name="$t('auditLog.allWorkspaces')"
              :not-selected-text="$t('auditLog.allWorkspaces')"
              @input="filterWorkspace"
            ></PaginatedDropdown>
          </FilterWrapper>
          <FilterWrapper :name="$t('auditLog.filterActionTypeTitle')">
            <PaginatedDropdown
              ref="typeFilter"
              :value="filters.action_type"
              :fetch-page="fetchActionTypes"
              :empty-item-display-name="$t('auditLog.allActionTypes')"
              :not-selected-text="$t('auditLog.allActionTypes')"
              @input="filterActionType"
            ></PaginatedDropdown>
          </FilterWrapper>
          <FilterWrapper :name="$t('auditLog.filterFromTimestampTitle')">
            <DateFilter
              ref="fromTimestampFilter"
              :placeholder="$t('auditLog.filterFromTimestamp')"
              :disable-dates="disableDates"
              @input="filterFromTimestamp"
            ></DateFilter>
          </FilterWrapper>
          <FilterWrapper :name="$t('auditLog.filterToTimestampTitle')">
            <DateFilter
              ref="toTimestampFilter"
              :placeholder="$t('auditLog.filterToTimestamp')"
              :disable-dates="disableDates"
              @input="filterToTimestamp"
            ></DateFilter>
          </FilterWrapper>
          <Button
            class="audit-log__clear-filters-button"
            type="secondary"
            @click="clearFilters"
          >
            {{ $t('auditLog.clearFilters') }}</Button
          >
        </div>
      </template>
    </CrudTable>
  </div>
</template>

<script>
import _ from 'lodash'
import moment from '@baserow/modules/core/moment'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import PaginatedDropdown from '@baserow/modules/core/components/PaginatedDropdown'
import AuditLogService from '@baserow_enterprise/services/auditLog'
import DateFilter from '@baserow_enterprise/components/crudTable/filters/DateFilter'
import FilterWrapper from '@baserow_enterprise/components/crudTable/filters/FilterWrapper'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import LongTextField from '@baserow_enterprise/components/crudTable/fields/LongTextField'
import AuditLogExportModal from '@baserow_enterprise/components/admin/modals/AuditLogExportModal'
import EnterpriseFeatures from '@baserow_enterprise/features'

function initFilters(workspaceId = null) {
  const filters = {}
  if (workspaceId !== null) {
    filters.workspace_id = workspaceId
  }
  return filters
}

export default {
  name: 'AuditLog',
  components: {
    AuditLogExportModal,
    CrudTable,
    PaginatedDropdown,
    DateFilter,
    FilterWrapper,
  },
  layout: 'app',
  middleware: 'authenticated',
  asyncData({ app, error, route, store }) {
    const workspaceId = route.params.workspaceId
      ? parseInt(route.params.workspaceId)
      : null
    if (workspaceId) {
      if (!app.$hasFeature(EnterpriseFeatures.AUDIT_LOG, workspaceId)) {
        return error({
          statusCode: 401,
          message: 'Available in the advanced/enterprise version',
        })
      } else if (
        !app.$hasPermission(
          'workspace.list_audit_log_entries',
          store.getters['workspace/get'](workspaceId),
          workspaceId
        )
      ) {
        return error({ statusCode: 404, message: 'Page not found' })
      }
    } else if (!app.$hasFeature(EnterpriseFeatures.AUDIT_LOG)) {
      return error({
        statusCode: 401,
        message: 'Available in the advanced/enterprise version',
      })
    } else if (!store.getters['auth/isStaff']) {
      return error({ statusCode: 403, message: 'Forbidden.' })
    }

    return { workspaceId }
  },
  data() {
    const params = this.$route.params
    const workspaceId = params.workspaceId ? parseInt(params.workspaceId) : null
    const filters = initFilters(workspaceId)

    const columns = [
      new CrudTableColumn(
        'user',
        () => this.$t('auditLog.user'),
        SimpleField,
        true,
        false,
        false,
        {},
        '15'
      ),
    ]

    if (!workspaceId) {
      columns.push(
        new CrudTableColumn(
          'workspace',
          () => this.$t('auditLog.workspace'),
          SimpleField,
          true,
          false,
          false,
          {},
          '15'
        )
      )
    }

    columns.push(
      ...[
        new CrudTableColumn(
          'type',
          () => this.$t('auditLog.actionType'),
          SimpleField,
          true,
          false,
          false,
          {},
          '10'
        ),
        new CrudTableColumn(
          'description',
          () => this.$t('auditLog.description'),
          LongTextField,
          false,
          false,
          false,
          {},
          '40'
        ),
        new CrudTableColumn(
          'timestamp',
          () => this.$t('auditLog.timestamp'),
          LocalDateField,
          true,
          false,
          false,
          { dateTimeFormat: 'L LTS' },
          '10'
        ),
        new CrudTableColumn(
          'ip_address',
          () => this.$t('auditLog.ip_address'),
          SimpleField,
          true,
          false,
          false,
          {},
          '10'
        ),
      ]
    )

    this.columns = columns
    this.service = AuditLogService(this.$client)

    return {
      filters,
      dateTimeFormat: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
    }
  },
  computed: {
    workspaceName() {
      const selectedWorkspace = this.$store.getters['workspace/get'](
        this.workspaceId
      )
      return selectedWorkspace ? selectedWorkspace.name : ''
    },
    disableDates() {
      const minimumDate = moment('2023-01-01', 'YYYY-MM-DD')
      const maximumDate = moment().add(1, 'day').endOf('day')
      return {
        to: minimumDate.toDate(),
        from: maximumDate.toDate(),
      }
    },
    selectedWorkspaceId() {
      try {
        return this.$store.getters['workspace/selectedId']
      } catch (e) {
        return null
      }
    },
  },
  watch: {
    selectedWorkspaceId(newValue, oldValue) {
      if (newValue !== oldValue && this.workspaceId) {
        this.$router.push({
          name: newValue ? 'workspace-audit-log' : 'dashboard',
          params: { workspaceId: newValue },
        })
      }
    },
  },
  methods: {
    clearFilters() {
      for (const filterRef of [
        'userFilter',
        'workspaceFilter',
        'typeFilter',
        'fromTimestampFilter',
        'toTimestampFilter',
      ]) {
        this.$refs[filterRef]?.clear()
      }
      this.filters = initFilters(this.workspaceId)
    },
    setFilter(key, value) {
      // Remove or add the filter reactively.
      if (value == null) {
        if (this.filters[key] !== undefined) {
          this.filters = _.pickBy(this.filters, (v, k) => {
            return key !== k
          })
        }
      } else {
        this.filters = { ...this.filters, [key]: value }
      }
    },
    filterUser(userId) {
      this.setFilter('user_id', userId)
    },
    fetchUsers(page, search) {
      return this.service.fetchUsers(page, search, this.workspaceId)
    },
    filterWorkspace(workspaceId) {
      this.setFilter('workspace_id', workspaceId)
    },
    fetchWorkspaces(page, search) {
      return this.service.fetchWorkspaces(page, search)
    },
    fetchActionTypes(page, search) {
      return this.service.fetchActionTypes(page, search, this.workspaceId)
    },
    filterActionType(actionTypeId) {
      this.setFilter('action_type', actionTypeId)
    },
    filterFromTimestamp(fromTimestamp) {
      if (fromTimestamp && moment(fromTimestamp).isValid()) {
        this.setFilter(
          'from_timestamp',
          moment(fromTimestamp).startOf('day').format(this.dateTimeFormat)
        )
      } else if (!fromTimestamp) {
        this.setFilter('from_timestamp', null)
      }
    },
    filterToTimestamp(toTimestamp) {
      if (toTimestamp && moment(toTimestamp).isValid()) {
        this.setFilter(
          'to_timestamp',
          moment(toTimestamp).endOf('day').format(this.dateTimeFormat)
        )
      } else if (!toTimestamp) {
        this.setFilter('to_timestamp', null)
      }
    },
  },
}
</script>
