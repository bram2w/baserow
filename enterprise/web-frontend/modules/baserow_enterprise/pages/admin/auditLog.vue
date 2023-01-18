<template>
  <div class="audit-log__table">
    <AuditLogExportModal
      ref="exportModal"
      :filters="filters"
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
        {{ $t('auditLog.title') }}
      </template>
      <template #header-right-side>
        <button
          class="button button--large"
          @click.prevent="$refs.exportModal.show()"
        >
          {{ $t('auditLog.exportToCsv') }}
        </button>
      </template>
      <template #header-filters>
        <div class="audit-log__filters">
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
          <FilterWrapper :name="$t('auditLog.filterGroupTitle')">
            <PaginatedDropdown
              ref="groupFilter"
              :value="filters.group_id"
              :fetch-page="fetchGroups"
              :empty-item-display-name="$t('auditLog.allGroups')"
              :not-selected-text="$t('auditLog.allGroups')"
              @input="filterGroup"
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
          <button
            class="audit-log__clear_filters_button button button--ghost"
            @click="clearFilters"
          >
            {{ $t('auditLog.clearFilters') }}
          </button>
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
import AuditLogAdminService from '@baserow_enterprise/services/auditLogAdmin'
import DateFilter from '@baserow_enterprise/components/crudTable/filters/DateFilter'
import FilterWrapper from '@baserow_enterprise/components/crudTable/filters/FilterWrapper'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import LongTextField from '@baserow_enterprise/components/crudTable/fields/LongTextField'
import AuditLogExportModal from '@baserow_enterprise/components/admin/modals/AuditLogExportModal'

export default {
  name: 'AuditLogAdminTable',
  components: {
    AuditLogExportModal,
    CrudTable,
    PaginatedDropdown,
    DateFilter,
    FilterWrapper,
  },
  layout: 'app',
  middleware: 'staff',
  data() {
    this.columns = [
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
      new CrudTableColumn(
        'group',
        () => this.$t('auditLog.group'),
        SimpleField,
        true,
        false,
        false,
        {},
        '15'
      ),
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
    this.service = AuditLogAdminService(this.$client)
    return {
      filters: {},
      dateTimeFormat: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
    }
  },
  computed: {
    disableDates() {
      const minimumDate = moment('2023-01-01', 'YYYY-MM-DD')
      const maximumDate = moment().add(1, 'day').endOf('day')
      return {
        to: minimumDate.toDate(),
        from: maximumDate.toDate(),
      }
    },
  },
  methods: {
    clearFilters() {
      for (const filterRef of [
        'userFilter',
        'groupFilter',
        'typeFilter',
        'fromTimestampFilter',
        'toTimestampFilter',
      ]) {
        this.$refs[filterRef].clear()
      }
      this.filters = {}
    },
    setFilter(key, value) {
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
    filterUser(user) {
      this.setFilter('user_id', user.id)
    },
    fetchUsers(page, search) {
      return this.service.fetchUsers(page, search)
    },
    filterGroup(group) {
      this.setFilter('group_id', group.id)
    },
    fetchGroups(page, search) {
      return this.service.fetchGroups(page, search)
    },
    fetchActionTypes(page, search) {
      return this.service.fetchActionTypes(page, search)
    },
    filterActionType(actionType) {
      this.setFilter('action_type', actionType.id)
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
