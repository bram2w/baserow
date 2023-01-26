<template>
  <Modal>
    <h2 class="box__title">
      {{ application.name }} {{ $t('snapshotsModal.title') }}
    </h2>
    <p>
      {{ $t('snapshotsModal.description') }}
      <span v-if="maxSnapshots >= 0">{{
        $tc('snapshotsModal.descriptionLimits', maxSnapshots)
      }}</span>
    </p>
    <Error :error="error"></Error>
    <div class="snapshots-modal">
      <CreateSnapshotForm
        v-if="!limitReached"
        ref="form"
        :snapshots="snapshots"
        @submitted="submitted"
      >
        <template v-if="jobIsRunning || jobHasSucceeded" #input>
          <ProgressBar
            :value="job.progress_percentage"
            :status="jobHumanReadableState"
          />
        </template>
        <template #default>
          <button
            v-if="!createFinished"
            :class="{ 'button--loading': createLoading }"
            class="button"
            :disabled="createLoading"
          >
            {{ $t('snapshotsModal.create') }}
          </button>
          <a v-else class="button button--ghost" @click="reset()">
            {{ $t('snapshotsModal.reset') }}
          </a>
        </template>
      </CreateSnapshotForm>
      <div v-else>
        {{ $t('snapshotsModal.limitReached') }}
      </div>
      <div v-if="snapshotsLoading" class="loading"></div>
      <div v-if="snapshots.length > 0" class="snapshots-modal__list">
        <SnapshotListItem
          v-for="snapshot in snapshots"
          :key="snapshot.id"
          :snapshot="snapshot"
          @snapshot-deleted="snapshotDeleted"
        ></SnapshotListItem>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import CreateSnapshotForm from '@baserow/modules/core/components/snapshots/CreateSnapshotForm'
import SnapshotListItem from '@baserow/modules/core/components/snapshots/SnapshotListItem'
import SnapshotsService from '@baserow/modules/core/services/snapshots'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'SnapshotsModal',
  components: {
    CreateSnapshotForm,
    SnapshotListItem,
  },
  mixins: [modal, error, jobProgress],
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      createLoading: false,
      createFinished: false,
      snapshotsLoading: false,
      snapshots: [],
      // Currently we don't query the backend to fetch the limit
      limitReached: false,
    }
  },
  computed: {
    maxSnapshots() {
      return parseInt(this.$env.BASEROW_MAX_SNAPSHOTS_PER_GROUP)
    },
  },
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    async show(...args) {
      this.hideError()
      await this.loadSnapshots()
      modal.methods.show.bind(this)(...args)
    },
    async submitted(values) {
      this.createLoading = true
      this.hideError()
      try {
        const { data } = await SnapshotsService(this.$client).create(
          this.application.id,
          values
        )
        this.startJobPoller(data)
      } catch (error) {
        this.createLoading = false
        this.handleError(error)
      }
    },
    async onJobDone() {
      this.createLoading = false
      this.createFinished = true
      await this.loadSnapshots()
    },
    // eslint-disable-next-line require-await
    async onJobFailed() {
      this.createLoading = false
      this.showError(
        this.$t('clientHandler.notCompletedTitle'),
        this.job.human_readable_error
      )
    },
    // eslint-disable-next-line require-await
    async onJobPollingError(error) {
      this.createLoading = false
      notifyIf(error)
    },
    async loadSnapshots() {
      this.snapshotsLoading = true
      this.snapshots = []
      try {
        const { data } = await SnapshotsService(this.$client).list(
          this.application.id
        )
        this.snapshots = data
      } catch (error) {
        this.handleError(error)
      } finally {
        this.snapshotsLoading = false
      }
    },
    snapshotDeleted(deletedSnapshot) {
      this.snapshots = this.snapshots.filter(
        (snapshot) => snapshot.id !== deletedSnapshot.id
      )
    },
    reset() {
      this.stopPollIfRunning()
      this.job = null
      this.createFinished = false
      this.createLoading = false
      this.$refs.form.resetName()
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
