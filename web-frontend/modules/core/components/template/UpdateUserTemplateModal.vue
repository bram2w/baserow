<template>
  <Modal
    ref="modal"
    class="user-template-modal-wrapper"
    :box-padding="false"
    :close-button="false"
    @hidden="$emit('hidden')"
  >
    <div class="user-template-modal">
      <div class="user-template-modal__head">
        <h2 class="user-template-modal__title">
          {{
            activeMode === 'details'
              ? $t('updateUserTemplateModal.detailsTitle')
              : $t('updateUserTemplateModal.contentTitle')
          }}
        </h2>
        <button
          type="button"
          class="user-template-modal__head-action"
          :title="$t('action.close')"
          @click="hide()"
        >
          <i class="iconoir-cancel"></i>
        </button>
      </div>

      <div class="user-template-modal__body">
        <p class="user-template-modal__description">
          {{
            activeMode === 'details'
              ? $t('updateUserTemplateModal.detailsDescription')
              : $t('updateUserTemplateModal.contentDescription')
          }}
        </p>
        <UserTemplateDetailsForm
          v-if="activeMode === 'details'"
          ref="detailsForm"
          :model-value="details"
          :categories="formCategories"
          :show-errors="submitted"
          :disabled="jobIsRunning || updateLoading"
          @update:model-value="Object.assign(values, $event)"
        />
        <UserTemplateContentForm
          v-else
          :model-value="content"
          :preselect="preselect"
          :disabled="jobIsRunning || updateLoading"
          @update:model-value="Object.assign(values, $event)"
          @update:valid="contentValid = $event"
        />

        <Error :error="error" class="margin-bottom-0"></Error>
      </div>

      <div class="user-template-modal__footer">
        <div
          v-if="jobIsRunning || jobIsFinished"
          class="user-template-modal__progress"
        >
          <ProgressBar
            :value="job.progress_percentage"
            :status="jobHumanReadableState"
          />
        </div>
        <div
          v-else-if="activeMode === 'content'"
          class="user-template-modal__selected"
        >
          {{
            $t('userTemplateContentForm.selectedApplications', {
              count: values.applicationIds.length,
            })
          }}
        </div>
        <div class="user-template-modal__footer-actions">
          <ButtonText
            v-if="jobIsRunning || cancelLoading"
            tag="a"
            type="secondary"
            class="modal-progress__cancel-button"
            :loading="cancelLoading"
            @click="cancelJob"
          >
            {{ $t('action.cancel') }}
          </ButtonText>
          <Button v-else type="secondary" @click="hide()">
            {{ $t('action.cancel') }}
          </Button>
          <Button
            type="primary"
            :loading="updateLoading || jobIsRunning || jobIsFinished"
            :disabled="!canUpdate"
            @click="update"
          >
            {{
              activeMode === 'details'
                ? $t('updateUserTemplateModal.save')
                : $t('updateUserTemplateModal.update')
            }}
          </Button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import { toRaw } from 'vue'
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import job from '@baserow/modules/core/mixins/job'
import JobService from '@baserow/modules/core/services/job'
import { CreateUserTemplateJobType } from '@baserow/modules/core/jobTypes'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import { DEFAULT_TEMPLATE_ICON } from '@baserow/modules/core/utils/templateIcons'
import UserTemplateContentForm from '@baserow/modules/core/components/template/UserTemplateContentForm'
import UserTemplateDetailsForm from '@baserow/modules/core/components/template/UserTemplateDetailsForm'

// The notifications of the jobs that ended, by job of the store. The same template
// can be updated from more than one mounted modal, which all follow the same job,
// but the author is notified once.
const notifiedJobs = new WeakMap()

/**
 * Updates the details or the content of a template of the user. Either commits a
 * new revision of the template through a `create_user_template` job.
 */
export default {
  name: 'UpdateUserTemplateModal',
  components: { UserTemplateContentForm, UserTemplateDetailsForm },
  mixins: [modal, error, job],
  props: {
    // The template as listed in the user's templates, with the details of its
    // latest revision.
    template: {
      type: Object,
      required: true,
    },
    // Whether the details or the content are updated when no job is running.
    mode: {
      type: String,
      required: true,
      validator: (value) => ['details', 'content'].includes(value),
    },
    // The categories an author can pick from, each with an `id` and a `name`.
    categories: {
      type: Array,
      required: true,
    },
  },
  emits: ['updated', 'hidden'],
  data() {
    return {
      // The mode of the running job, or else the requested one.
      activeMode: this.mode,
      // The errors of the details show after the first attempt to save.
      submitted: false,
      updateLoading: false,
      // Whether the content form allows to update the template.
      contentValid: false,
      values: this.getDefaultValues(),
    }
  },
  computed: {
    details() {
      const { icon, name, description, categoryIds } = this.values
      return { icon, name, description, categoryIds }
    },
    content() {
      const { workspaceId, applicationIds } = this.values
      return { workspaceId, applicationIds }
    },
    // The template keeps a category that can't be picked anymore, unless the
    // author removes it.
    formCategories() {
      const missing = this.template.categories.filter(
        (category) => !this.categories.some(({ id }) => id === category.id)
      )
      return [...this.categories, ...missing]
    },
    // The content is copied from the same workspace and applications as before,
    // if known.
    preselect() {
      if (!this.template.source_workspace_id) {
        return null
      }
      return {
        workspaceId: this.template.source_workspace_id,
        applicationIds: this.template.source_application_ids || [],
      }
    },
    detailsChanged() {
      const initial = this.getTemplateDetails()
      const sorted = (ids) => [...ids].sort((a, b) => a - b).join(',')
      return (
        this.values.name.trim() !== initial.name ||
        this.values.description.trim() !== initial.description ||
        this.values.icon !== initial.icon ||
        sorted(this.values.categoryIds) !== sorted(initial.categoryIds)
      )
    },
    canUpdate() {
      const valid =
        this.activeMode === 'details' ? this.detailsChanged : this.contentValid
      return (
        valid &&
        !this.updateLoading &&
        !this.jobIsRunning &&
        !this.jobIsFinished
      )
    },
  },
  methods: {
    show(...args) {
      // A running job is shown again instead of an empty form. A job that failed
      // while the modal was closed is shown once with its error and inputs, when
      // the same is updated again. An update still being sent keeps its inputs.
      if (this.job?.state === 'failed' && this.activeMode === this.mode) {
        this.job = null
      } else if (!this.jobIsRunning && !this.updateLoading) {
        this.reset()
        this.restoreRunningJob()
      }
      modal.methods.show.call(this, ...args)
    },
    getTemplateDetails() {
      return {
        icon: this.template.icon || DEFAULT_TEMPLATE_ICON,
        name: this.template.name,
        description: this.template.description || '',
        categoryIds: this.template.categories.map((category) => category.id),
      }
    },
    getDefaultValues() {
      return {
        ...this.getTemplateDetails(),
        // The content form selects a workspace when it's shown.
        workspaceId: null,
        applicationIds: [],
      }
    },
    reset() {
      this.activeMode = this.mode
      this.submitted = false
      this.updateLoading = false
      this.contentValid = false
      this.job = null
      this.values = this.getDefaultValues()
      this.hideError()
    },
    restoreRunningJob() {
      const runningJob = this.$store.getters['job/getUnfinishedJobs'].find(
        (job) =>
          job.type === CreateUserTemplateJobType.getType() &&
          job.template === this.template.id
      )
      if (!runningJob) {
        return
      }
      this.job = runningJob
      // Only a content update copies applications.
      this.activeMode =
        runningJob.application_ids.length > 0 ? 'content' : 'details'
      this.values = {
        icon: runningJob.icon,
        name: runningJob.name,
        description: runningJob.description,
        categoryIds: [...runningJob.category_ids],
        workspaceId: runningJob.workspace_id,
        applicationIds: [...runningJob.application_ids],
      }
    },
    getRequest() {
      if (this.activeMode === 'details') {
        return {
          template_id: this.template.id,
          name: this.values.name.trim(),
          description: this.values.description.trim(),
          icon: this.values.icon,
          category_ids: this.values.categoryIds,
        }
      }
      return {
        template_id: this.template.id,
        workspace_id: this.values.workspaceId,
        application_ids: this.values.applicationIds,
      }
    },
    async update() {
      if (this.activeMode === 'details') {
        this.submitted = true
        if (!this.$refs.detailsForm.isValid()) {
          return
        }
      }
      if (!this.canUpdate) {
        return
      }
      this.updateLoading = true
      this.hideError()
      try {
        const { data } = await JobService(this.$client).create(
          CreateUserTemplateJobType.getType(),
          this.getRequest()
        )
        await this.createAndMonitorJob(data)
      } catch (error) {
        this.handleError(error, 'template', this.getSpecificErrorMap())
      } finally {
        this.updateLoading = false
      }
    },
    async onJobFinished() {
      await this.handleUpdated(
        'toast/success',
        'updateUserTemplateModal.updated'
      )
    },
    // The details are kept by a content update, so the author can only fix them
    // with "Edit details".
    getSpecificErrorMap() {
      if (this.activeMode === 'details') {
        return null
      }
      const message = new ResponseErrorMessage(
        this.$t('clientHandler.notCompletedTitle'),
        this.$t('updateUserTemplateModal.invalidKeptDetails')
      )
      return {
        ERROR_INVALID_TEMPLATE_CATEGORY: message,
        ERROR_INVALID_TEMPLATE_ICON: message,
      }
    },
    // Notifies the author once per job, however many modals follow it.
    notify(job, notification) {
      const key = toRaw(job)
      if (!notifiedJobs.has(key)) {
        notifiedJobs.set(key, notification())
      }
      return notifiedJobs.get(key)
    },
    async handleUpdated(toast, title) {
      const finishedJob = this.job
      this.hide()
      this.reset()
      await this.notify(finishedJob, async () => {
        this.$store.dispatch(toast, { title: this.$t(title) })
        // The workspace of the new revision can only be previewed once the
        // `workspace_template_ids` of the permissions are refreshed.
        await this.$store.dispatch('auth/refresh').catch(() => {})
      })
      this.$emit('updated', finishedJob)
    },
    onJobFailed() {
      if (this.job.revision) {
        // It failed after the revision was committed, which is kept.
        this.handleUpdated(
          'toast/warning',
          'updateUserTemplateModal.failedAfterUpdated'
        )
        return
      }
      const title = this.$t('clientHandler.notCompletedTitle')
      const message = this.job.human_readable_error
      this.showError(title, message)
      // The error isn't seen while the modal is closed.
      if (!this.$refs.modal?.open) {
        this.notify(this.job, () =>
          this.$store.dispatch('toast/error', { title, message })
        )
      }
    },
    onJobCancelled() {
      // The inputs are kept, so that the author can try again.
      this.job = null
    },
    getCustomHumanReadableJobState() {
      return ''
    },
    getJobNotCancellableMessage() {
      return this.$t('updateUserTemplateModal.cannotBeCancelled')
    },
  },
}
</script>
