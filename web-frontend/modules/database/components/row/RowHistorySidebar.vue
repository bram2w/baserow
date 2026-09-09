<template>
  <div>
    <div
      v-if="!loaded && loading && entries.length === 0 && !historyLoadFailed"
      class="loading-absolute-center"
    />
    <template v-else>
      <div class="row-history">
        <Alert v-if="historyLoadFailed" type="error">
          <p>{{ $t('rowHistorySidebar.loadError') }}</p>
          <template #actions>
            <Button
              type="secondary"
              size="small"
              :loading="loading"
              @click="initialLoad(true)"
            >
              {{ $t('action.retry') }}
            </Button>
          </template>
        </Alert>
        <div v-if="entriesWithContents.length > 0">
          <InfiniteScroll
            ref="infiniteScroll"
            :current-count="currentCount"
            :max-count="totalCount"
            :loading="loading"
            :reverse="true"
            :render-end="false"
            @load-next-page="loadNextPage"
          >
            <template #default>
              <div
                v-for="(entry, index) in entriesWithContents"
                :key="entry.id"
              >
                <div
                  v-if="
                    shouldDisplayDateSeparator(
                      entriesWithContents,
                      'timestamp',
                      index
                    )
                  "
                  class="row-history__day-separator"
                >
                  <span>{{ formatDateSeparator(entry.timestamp) }}</span>
                </div>
                <RowHistoryEntry
                  :entry="entry"
                  :workspace-id="database.workspace.id"
                  :fields="fields"
                  :class="{
                    'row-history-entry--first':
                      index === 0 ||
                      shouldDisplayDateSeparator(
                        entriesWithContents,
                        'timestamp',
                        index - 1
                      ),
                  }"
                >
                </RowHistoryEntry>
              </div>
            </template>
          </InfiniteScroll>
        </div>
        <div v-else-if="!historyLoadFailed" class="row-history__empty">
          <i class="row-history__empty-icon baserow-icon-history"></i>
          <div class="row-history__empty-text">
            {{ $t('rowHistorySidebar.empty') }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import {
  shouldDisplayDateSeparator,
  formatDateSeparator,
} from '@baserow/modules/database/utils/date'
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
    fields: {
      type: Array,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      historyLoadFailed: false,
    }
  },
  computed: {
    ...mapGetters({
      entries: 'rowHistory/getSortedEntries',
      loading: 'rowHistory/getLoading',
      loaded: 'rowHistory/getLoaded',
      currentCount: 'rowHistory/getCurrentCount',
      totalCount: 'rowHistory/getTotalCount',
      historyRevision: 'rowHistory/getRevision',
    }),
    entriesWithContents() {
      const fieldIds = this.fields.map((f) => f.id)

      const entriesToRender = this.entries.filter((entry) => {
        const entryFields = new Set(
          Object.keys(entry.before).concat(Object.keys(entry.after))
        )
        const validEntryFieldIds = [...entryFields]
          .map((fieldIdentifier) => entry.fields_metadata[fieldIdentifier]?.id)
          .filter((entryFieldId) => fieldIds.includes(entryFieldId))
        return (
          validEntryFieldIds.length > 0 || entry.action_type !== 'update_rows'
        )
      })

      return entriesToRender
    },
  },
  watch: {
    historyRevision() {
      this.initialLoad(true)
    },
    row(newRow, oldRow) {
      this.historyLoadFailed = false
      this.initialLoad()
    },
  },
  async created() {
    await this.initialLoad()
  },
  beforeUnmount() {
    this._historyLoad = null
  },
  methods: {
    async initialLoad(realtimeRecovery = false) {
      realtimeRecovery ||= this.historyRevision > 0 && !this.loaded
      const tableId = this.table.id
      const rowId = this.row.id
      if (!Number.isInteger(rowId)) {
        return
      }
      const key = `${tableId}:${rowId}`
      if (this._historyLoad?.key === key) {
        this._historyLoad.repeat = true
        this._historyLoad.realtimeRecovery ||= realtimeRecovery
        return
      }
      const request = { key, repeat: false, realtimeRecovery }
      this._historyLoad = request
      try {
        do {
          request.repeat = false
          await this.$store.dispatch('rowHistory/fetchInitial', {
            tableId,
            rowId,
            realtimeRecovery: request.realtimeRecovery,
          })
          // Reconnects during a request need one trailing snapshot, never a
          // parallel request per notification. Unmounted/previous rows stop here.
        } while (request.repeat && this._historyLoad === request)
        if (this._historyLoad === request) {
          this.historyLoadFailed = false
        }
      } catch (e) {
        if (this._historyLoad === request) {
          this.historyLoadFailed = true
        }
      } finally {
        if (this._historyLoad === request) {
          this._historyLoad = null
        }
      }
    },
    async loadNextPage() {
      try {
        const tableId = this.table.id
        const rowId = this.row.id
        await this.$store.dispatch('rowHistory/fetchNextPage', {
          tableId,
          rowId,
        })
      } catch (e) {
        notifyIf(e, 'application')
      }
    },
    shouldDisplayDateSeparator,
    formatDateSeparator,
  },
}
</script>
