<template>
  <div>
    <div v-if="!loaded && loading" class="loading-absolute-center" />
    <template v-else>
      <div class="row-history">
        <div v-if="totalCount > 0">
          <InfiniteScroll
            ref="infiniteScroll"
            :current-count="currentCount"
            :max-count="totalCount"
            :loading="loading"
            :reverse="true"
            :render-end="false"
          >
            <template #default>
              <RowHistoryEntry
                v-for="entry in entries"
                :key="entry.id"
                :entry="entry"
              >
              </RowHistoryEntry>
            </template>
          </InfiniteScroll>
        </div>
        <div v-else class="row-history__empty">
          <i class="row-history__empty-icon fas fa-history"></i>
          <div class="row-history__empty-text">
            {{ $t('rowHistorySidebar.empty') }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import InfiniteScroll from '@baserow/modules/core/components/helpers/InfiniteScroll'
import RowHistoryEntry from '@baserow/modules/database/components/row/RowHistoryEntry.vue'

export default {
  name: 'RowHistorySidebar',
  components: {
    InfiniteScroll,
    RowHistoryEntry,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      entries: 'rowHistory/getSortedEntries',
      loading: 'rowHistory/getLoading',
      loaded: 'rowHistory/getLoaded',
      currentCount: 'rowHistory/getCurrentCount',
      totalCount: 'rowHistory/getTotalCount',
    }),
  },
  async created() {
    await this.initialLoad()
  },
  methods: {
    async initialLoad() {
      try {
        const tableId = this.table.id
        const rowId = this.row.id
        await this.$store.dispatch('rowHistory/fetchInitial', {
          tableId,
          rowId,
        })
      } catch (e) {
        notifyIf(e, 'application')
      }
    },
  },
}
</script>
