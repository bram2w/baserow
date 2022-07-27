<template>
  <div class="snapshots-modal__snapshot">
    <div class="snapshots-modal__info">
      <div v-if="!jobIsRunning && !jobHasSucceeded">
        <div class="snapshots-modal__name">
          {{ snapshot.name }}
        </div>
        <div class="snapshots-modal__detail">
          {{ snapshot.created_by ? `${snapshot.created_by.username} - ` : '' }}
          {{ $t('snapshotListItem.created') }} {{ humanCreatedAt }}
        </div>
      </div>
      <ProgressBar
        v-else
        :value="job.progress_percentage"
        :status="jobHumanReadableState"
      />
    </div>
    <div class="snapshots-modal__actions">
      <a
        :class="{ 'snapshots-modal__restore--loading': restoreLoading }"
        @click="restore"
        >{{ $t('snapshotListItem.restore') }}</a
      >
      <a class="snapshots-modal__delete" @click="showDelete">{{
        $t('snapshotListItem.delete')
      }}</a>
      <DeleteSnapshotModal
        ref="deleteSnapshotModal"
        :snapshot="snapshot"
        @snapshot-deleted="$emit('snapshot-deleted', $event)"
      ></DeleteSnapshotModal>
    </div>
  </div>
</template>

<script>
import SnapshotsService from '@baserow/modules/core/services/snapshots'
import DeleteSnapshotModal from '@baserow/modules/core/components/snapshots/DeleteSnapshotModal'
import { getHumanPeriodAgoCount } from '@baserow/modules/core/utils/date'
import { notifyIf } from '@baserow/modules/core/utils/error'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'

export default {
  components: {
    DeleteSnapshotModal,
  },
  mixins: [jobProgress],
  props: {
    snapshot: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      restoreLoading: false,
      restoreFinished: false,
    }
  },
  computed: {
    humanCreatedAt() {
      const { period, count } = getHumanPeriodAgoCount(this.snapshot.created_at)
      return this.$tc(`datetime.${period}Ago`, count)
    },
  },
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    async restore() {
      this.restoreLoading = true
      try {
        const { data } = await SnapshotsService(this.$client).restore(
          this.snapshot.id
        )
        this.startJobPoller(data)
      } catch (error) {
        this.restoreLoading = false
        notifyIf(error)
      }
    },
    showDelete() {
      this.$refs.deleteSnapshotModal.show()
    },
    // eslint-disable-next-line require-await
    async onJobDone() {
      this.restoreLoading = false
      this.restoreFinished = true
    },
    // eslint-disable-next-line require-await
    async onJobFailed() {
      this.restoreLoading = false
      this.showError(
        this.$t('clientHandler.notCompletedTitle'),
        this.$t('clientHandler.notCompletedDescription')
      )
    },
    // eslint-disable-next-line require-await
    async onJobPollingError(error) {
      this.restoreLoading = false
      notifyIf(error)
    },
    getCustomHumanReadableJobState(jobState) {
      if (jobState.startsWith('importing')) {
        return this.$t('snapshotsModal.importingState')
      }
      return ''
    },
  },
}
</script>
