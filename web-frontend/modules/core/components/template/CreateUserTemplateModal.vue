<template>
  <Modal
    ref="modal"
    small
    :box-padding="false"
    :close-button="false"
    @hidden="$emit('hidden')"
  >
    <div class="create-user-template-modal">
      <div class="create-user-template-modal__head">
        <button
          v-if="step === 'content'"
          type="button"
          class="create-user-template-modal__head-action create-user-template-modal__back"
          :disabled="jobIsRunning"
          @click="goToDetails"
        >
          <i class="iconoir-nav-arrow-left"></i>
        </button>
        <h2 class="create-user-template-modal__title">
          {{
            step === 'details'
              ? $t('createUserTemplateModal.detailsTitle')
              : $t('createUserTemplateModal.contentTitle')
          }}
        </h2>
        <button
          type="button"
          class="create-user-template-modal__head-action"
          :title="$t('action.close')"
          @click="hide()"
        >
          <i class="iconoir-cancel"></i>
        </button>
      </div>

      <template v-if="step === 'details'">
        <div class="create-user-template-modal__body">
          <p class="create-user-template-modal__description">
            {{ $t('createUserTemplateModal.detailsDescription') }}
          </p>

          <FormGroup
            :label="$t('createUserTemplateModal.name')"
            small-label
            required
            :error-message="nameError"
            class="margin-bottom-2"
          >
            <div class="create-user-template-modal__name">
              <button
                ref="iconButton"
                type="button"
                class="create-user-template-modal__icon-button"
                :title="$t('createUserTemplateModal.chooseIcon')"
                @click="
                  $refs.iconContext.toggle(
                    $refs.iconButton,
                    'bottom',
                    'left',
                    4
                  )
                "
              >
                <i :class="values.icon"></i>
                <i
                  class="create-user-template-modal__icon-button-arrow iconoir-nav-arrow-down"
                ></i>
              </button>
              <FormInput
                v-model="values.name"
                class="create-user-template-modal__name-input"
                :maxlength="nameMaxLength"
                :placeholder="$t('createUserTemplateModal.namePlaceholder')"
                :error="Boolean(nameError)"
              />
            </div>
            <TemplateIconSelectContext
              ref="iconContext"
              :active="values.icon"
              @selected="values.icon = $event"
            />
          </FormGroup>

          <FormGroup
            :label="$t('createUserTemplateModal.description')"
            small-label
            :helper-text="`${values.description.length} / ${descriptionMaxLength}`"
            class="margin-bottom-2"
          >
            <FormTextarea
              v-model="values.description"
              :rows="2"
              :maxlength="descriptionMaxLength"
              :placeholder="
                $t('createUserTemplateModal.descriptionPlaceholder')
              "
            />
          </FormGroup>

          <FormGroup
            :label="$t('createUserTemplateModal.categories')"
            small-label
            required
            :error-message="categoriesError"
          >
            <div class="create-user-template-modal__categories">
              <Chips
                v-for="category in categories"
                :key="category.id"
                type="button"
                size="small"
                :active="values.categoryIds.includes(category.id)"
                @click="toggleCategory(category.id)"
              >
                {{ category.name }}
              </Chips>
            </div>
          </FormGroup>
        </div>

        <div class="create-user-template-modal__footer">
          <div class="create-user-template-modal__footer-actions">
            <Button type="secondary" @click="hide()">
              {{ $t('action.cancel') }}
            </Button>
            <Button type="primary" @click="goToContent">
              {{ $t('createUserTemplateModal.continue') }}
            </Button>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="create-user-template-modal__body">
          <p class="create-user-template-modal__description">
            {{ $t('createUserTemplateModal.contentDescription') }}
          </p>

          <FormGroup
            :label="$t('createUserTemplateModal.workspace')"
            small-label
            required
            class="margin-bottom-2"
          >
            <Dropdown
              :model-value="values.workspaceId"
              :disabled="jobIsRunning"
              @update:model-value="chooseWorkspace"
            >
              <DropdownItem
                v-for="workspace in workspaces"
                :key="workspace.id"
                :name="workspace.name"
                :value="workspace.id"
                :disabled="!canExport(workspace)"
              />
            </Dropdown>
          </FormGroup>

          <ApplicationSelector
            v-if="selectedWorkspace"
            :key="selectedWorkspace.id"
            :workspace="selectedWorkspace"
            :selected-application-ids="values.applicationIds"
            :disabled="jobIsRunning"
            :title="$t('createUserTemplateModal.applications')"
            class="margin-bottom-2"
            @update="values.applicationIds = $event"
          />

          <Alert type="info-neutral" class="margin-bottom-0">
            <template #title>
              {{ $t('createUserTemplateModal.noticeTitle') }}
            </template>
            <ul class="create-user-template-modal__notice-list">
              <li>{{ $t('createUserTemplateModal.noticeSecrets') }}</li>
              <li>{{ $t('createUserTemplateModal.noticePeople') }}</li>
              <li>{{ $t('createUserTemplateModal.noticePersonalViews') }}</li>
              <li>{{ $t('createUserTemplateModal.noticeReferences') }}</li>
            </ul>
            <p>{{ $t('createUserTemplateModal.noticeRest') }}</p>
          </Alert>

          <Error :error="error" class="margin-bottom-0"></Error>
        </div>

        <div class="create-user-template-modal__footer">
          <div
            v-if="jobIsRunning || jobIsFinished"
            class="create-user-template-modal__progress"
          >
            <ProgressBar
              :value="job.progress_percentage"
              :status="jobHumanReadableState"
            />
          </div>
          <div v-else class="create-user-template-modal__selected">
            {{
              $t('createUserTemplateModal.selectedApplications', {
                count: values.applicationIds.length,
              })
            }}
          </div>
          <div class="create-user-template-modal__footer-actions">
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
              :loading="createLoading || jobIsRunning || jobIsFinished"
              :disabled="!canCreate"
              @click="create"
            >
              {{ $t('createUserTemplateModal.create') }}
            </Button>
          </div>
        </div>
      </template>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import job from '@baserow/modules/core/mixins/job'
import JobService from '@baserow/modules/core/services/job'
import { CreateUserTemplateJobType } from '@baserow/modules/core/jobTypes'
import { DEFAULT_TEMPLATE_ICON } from '@baserow/modules/core/utils/templateIcons'
import ApplicationSelector from '@baserow/modules/core/components/export/ApplicationSelector'
import TemplateIconSelectContext from '@baserow/modules/core/components/template/TemplateIconSelectContext'

// Mirrors the limits of the create request.
const NAME_MAX_LENGTH = 64
const DESCRIPTION_MAX_LENGTH = 80

export default {
  name: 'CreateUserTemplateModal',
  components: { ApplicationSelector, TemplateIconSelectContext },
  mixins: [modal, error, job],
  props: {
    // The categories an author can pick from, each with an `id` and a `name`.
    categories: {
      type: Array,
      required: true,
    },
  },
  emits: ['created', 'hidden'],
  data() {
    return {
      step: 'details',
      // The errors of the details step show after the first attempt to continue.
      detailsSubmitted: false,
      createLoading: false,
      // Whether the author picked the workspace, which must then stay selected.
      workspaceChosen: false,
      values: this.getDefaultValues(),
      nameMaxLength: NAME_MAX_LENGTH,
      descriptionMaxLength: DESCRIPTION_MAX_LENGTH,
    }
  },
  computed: {
    workspaces() {
      return this.$store.getters['workspace/getAllSorted']
    },
    selectedWorkspace() {
      return (
        this.workspaces.find(
          (workspace) => workspace.id === this.values.workspaceId
        ) || null
      )
    },
    nameError() {
      if (this.detailsSubmitted && this.values.name.trim() === '') {
        return this.$t('createUserTemplateModal.nameRequired')
      }
      return ''
    },
    categoriesError() {
      if (this.detailsSubmitted && this.values.categoryIds.length === 0) {
        return this.$t('createUserTemplateModal.categoriesRequired')
      }
      return ''
    },
    canCreate() {
      return (
        this.selectedWorkspace !== null &&
        this.canExport(this.selectedWorkspace) &&
        this.values.applicationIds.length > 0 &&
        !this.createLoading &&
        !this.jobIsRunning &&
        !this.jobIsFinished
      )
    },
  },
  methods: {
    show(...args) {
      // A running job is shown again instead of an empty form. A job that failed
      // while the modal was closed is shown once with its error and inputs.
      if (this.job?.state === 'failed') {
        this.job = null
      } else if (!this.jobIsRunning) {
        this.reset()
        this.restoreRunningJob()
      }
      this.loadPermissions()
      modal.methods.show.call(this, ...args)
    },
    getDefaultValues() {
      return {
        icon: DEFAULT_TEMPLATE_ICON,
        name: '',
        description: '',
        categoryIds: [],
        workspaceId: null,
        applicationIds: [],
      }
    },
    reset() {
      this.step = 'details'
      this.detailsSubmitted = false
      this.createLoading = false
      this.workspaceChosen = false
      this.job = null
      this.values = this.getDefaultValues()
      this.hideError()
      const selected = this.$store.getters['workspace/getSelected']
      this.selectWorkspace(selected?.id ?? this.workspaces[0]?.id ?? null)
    },
    restoreRunningJob() {
      const runningJob = this.$store.getters['job/getUnfinishedJobs'].find(
        (job) => job.type === CreateUserTemplateJobType.getType()
      )
      if (!runningJob) {
        return
      }
      this.job = runningJob
      this.step = 'content'
      this.values = {
        icon: runningJob.icon,
        name: runningJob.name,
        description: runningJob.description,
        categoryIds: [...runningJob.category_ids],
        workspaceId: runningJob.workspace_id,
        applicationIds: [...runningJob.application_ids],
      }
    },
    /**
     * The permissions of a workspace are only fetched when needed, so the ones of
     * the workspaces a template can be created from are fetched here. Until then
     * the global permissions are used and the backend checks again.
     */
    async loadPermissions() {
      await Promise.all(
        this.workspaces.map((workspace) =>
          this.$store
            .dispatch('workspace/fetchPermissions', workspace)
            .catch(() => {})
        )
      )
      if (
        this.jobIsRunning ||
        this.workspaceChosen ||
        this.canExport(this.selectedWorkspace)
      ) {
        return
      }
      const exportable = this.workspaces.find((workspace) =>
        this.canExport(workspace)
      )
      if (exportable) {
        this.selectWorkspace(exportable.id)
      }
    },
    canExport(workspace) {
      return (
        workspace !== null &&
        this.$hasPermission('workspace.export', workspace, workspace.id)
      )
    },
    chooseWorkspace(workspaceId) {
      this.workspaceChosen = true
      this.selectWorkspace(workspaceId)
    },
    /**
     * A different workspace has different applications, so the selection starts
     * again with all of them.
     */
    selectWorkspace(workspaceId) {
      this.values.workspaceId = workspaceId
      const workspace = this.selectedWorkspace
      this.values.applicationIds = workspace
        ? this.$store.getters['application/getAllOfWorkspace'](workspace).map(
            (application) => application.id
          )
        : []
    },
    toggleCategory(categoryId) {
      const index = this.values.categoryIds.indexOf(categoryId)
      if (index === -1) {
        this.values.categoryIds.push(categoryId)
      } else {
        this.values.categoryIds.splice(index, 1)
      }
    },
    goToContent() {
      this.detailsSubmitted = true
      if (this.nameError || this.categoriesError) {
        return
      }
      this.step = 'content'
    },
    goToDetails() {
      this.hideError()
      this.step = 'details'
    },
    async create() {
      if (!this.canCreate) {
        return
      }
      this.createLoading = true
      this.hideError()
      try {
        const { data } = await JobService(this.$client).create(
          CreateUserTemplateJobType.getType(),
          {
            workspace_id: this.values.workspaceId,
            application_ids: this.values.applicationIds,
            name: this.values.name.trim(),
            description: this.values.description,
            icon: this.values.icon,
            category_ids: this.values.categoryIds,
          }
        )
        await this.createAndMonitorJob(data)
      } catch (error) {
        this.handleError(error)
      } finally {
        this.createLoading = false
      }
    },
    onJobFinished() {
      this.$emit('created', this.job)
      this.hide()
      this.reset()
    },
    onJobFailed() {
      if (this.job.template) {
        // It failed after the template was created, which is kept. It's handled
        // as created, so that the author doesn't create it again.
        this.$store.dispatch('toast/warning', {
          title: this.$t('createUserTemplateModal.failedAfterCreated'),
        })
        this.onJobFinished()
        return
      }
      this.showError(
        this.$t('clientHandler.notCompletedTitle'),
        this.job.human_readable_error
      )
    },
    onJobCancelled() {
      // The inputs are kept, so that the author can try again.
      this.job = null
    },
    getCustomHumanReadableJobState() {
      return ''
    },
    getJobNotCancellableMessage() {
      return this.$t('createUserTemplateModal.cannotBeCancelled')
    },
  },
}
</script>
