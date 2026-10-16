<template>
  <Modal
    ref="modal"
    class="templates-modal"
    :full-screen="true"
    :close-button="false"
    keep-content
    @show="open = true"
    @hidden="hidden"
  >
    <div v-if="loading" class="loading-absolute-center"></div>
    <template v-else>
      <TemplateDetails
        v-if="selectedTemplate !== null"
        :key="selectedTemplate.id"
        :template="selectedTemplate"
        :categories="selectedTemplateCategories"
        :workspace="workspace"
        show-back
        class="templates__body"
        @back="selectedTemplate = null"
        @installed="hide()"
      ></TemplateDetails>
      <TemplateList
        v-show="selectedTemplate === null && tab === 'official'"
        :categories="categories"
        :active="open && selectedTemplate === null && tab === 'official'"
        class="templates__body"
        @selected="selectTemplate"
      >
        <template v-if="showTabs" #head>
          <SegmentControl
            :segments="tabs"
            :active-index="tabIndex"
            type="pills"
            @update:active-index="selectTab(tabs[$event].value)"
          ></SegmentControl>
        </template>
      </TemplateList>
      <UserTemplateList
        v-if="showTabs && userTemplatesOpened"
        v-show="selectedTemplate === null && tab === 'own'"
        ref="userTemplateList"
        :active="
          open && selectedTemplate === null && tab === 'own' && !creating
        "
        class="templates__body"
        @selected="selectTemplate"
        @create="openCreateModal"
      >
        <template #head>
          <SegmentControl
            :segments="tabs"
            :active-index="tabIndex"
            type="pills"
            @update:active-index="selectTab(tabs[$event].value)"
          ></SegmentControl>
        </template>
      </UserTemplateList>
      <div class="modal__actions">
        <a class="modal__close" @click="hide()">
          <i class="iconoir-cancel"></i>
        </a>
      </div>
    </template>
    <!-- Outside of the loaded content, so that a running job stays monitored
    when the modal is shown again. -->
    <CreateUserTemplateModal
      v-if="showTabs"
      ref="createUserTemplateModal"
      :categories="categories"
      @hidden="creating = false"
      @created="templateCreated"
    ></CreateUserTemplateModal>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import TemplateService from '@baserow/modules/core/services/template'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { FF_USER_TEMPLATES } from '@baserow/modules/core/plugins/featureFlags'

import CreateUserTemplateModal from '@baserow/modules/core/components/template/CreateUserTemplateModal'
import TemplateDetails from '@baserow/modules/core/components/template/TemplateDetails'
import TemplateList from '@baserow/modules/core/components/template/TemplateList'
import UserTemplateList from '@baserow/modules/core/components/template/UserTemplateList'

export default {
  name: 'TemplateModal',
  components: {
    CreateUserTemplateModal,
    TemplateDetails,
    TemplateList,
    UserTemplateList,
  },
  mixins: [modal],
  props: {
    // When no workspace is provided, the user must choose the workspace to install
    // the template into.
    workspace: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      // The content stays mounted while the modal is closed.
      open: false,
      loading: true,
      categories: [],
      selectedTemplate: null,
      tab: 'official',
      // The list of the user's templates is loaded when its tab is opened first.
      userTemplatesOpened: false,
      // While a template is created, its modal takes the search shortcut.
      creating: false,
    }
  },
  computed: {
    showTabs() {
      return (
        this.$featureFlagIsEnabled(FF_USER_TEMPLATES) &&
        this.$store.getters['auth/isAuthenticated']
      )
    },
    tabs() {
      return [
        {
          value: 'official',
          label: this.$t('templateModal.officialTemplates'),
          icon: 'baserow-icon-templates',
        },
        {
          value: 'own',
          label: this.$t('templateModal.yourTemplates'),
          icon: 'iconoir-box',
        },
      ]
    },
    tabIndex() {
      return this.tabs.findIndex((tab) => tab.value === this.tab)
    },
    selectedTemplateCategories() {
      // A user template lists its own categories.
      if (this.selectedTemplate.type === 'user') {
        return this.selectedTemplate.categories
      }
      return this.categories.filter((category) =>
        category.templates.some((t) => t.id === this.selectedTemplate.id)
      )
    },
  },
  watch: {
    open(open) {
      // The search of the page behind the modal closes all modals, so the modal keeps
      // the shortcut while it's open. The list and nested modals listen with a higher
      // priority.
      this.$priorityBus.$off('start-search', this.searchStarted)
      if (open) {
        this.$priorityBus.$on(
          'start-search',
          this.$priorityBus.level.MEDIUM,
          this.searchStarted
        )
      }
    },
  },
  beforeUnmount() {
    this.$priorityBus.$off('start-search', this.searchStarted)
  },
  methods: {
    /**
     * When the modal is opened we want to fetch all the templates and their
     * categories, so that the user can browse them. If a template id or slug is
     * provided, the details of that template are opened right away.
     */
    async show(templateId = null, ...args) {
      modal.methods.show.call(this, ...args)

      this.loading = true
      this.categories = []
      this.selectedTemplate = null
      this.tab = 'official'
      this.userTemplatesOpened = false

      try {
        const { data } = await TemplateService(this.$client).fetchAll()
        this.categories = data
        this.loading = false
      } catch (error) {
        notifyIf(error, 'templates')
        this.hide()
        return
      }

      if (templateId !== null) {
        const template = this.categories
          .flatMap((category) => category.templates)
          .find((t) => t.id === templateId || t.slug === templateId)
        if (template) {
          this.selectTemplate(template)
        }
      }
    },
    selectTab(tab) {
      this.tab = tab
      if (tab === 'own') {
        this.userTemplatesOpened = true
      }
    },
    selectTemplate(template) {
      this.selectedTemplate = template
    },
    openCreateModal() {
      this.creating = true
      this.$refs.createUserTemplateModal.show()
    },
    templateCreated() {
      this.$refs.userTemplateList?.refresh()
    },
    /**
     * Called however the modal is closed, also with escape or a click outside. The
     * content stays mounted, so the template is cleared to unmount its preview,
     * whose search would otherwise keep answering the shortcut.
     */
    hidden() {
      this.open = false
      this.selectedTemplate = null
    },
    searchStarted({ event }) {
      event.preventDefault()
    },
  },
}
</script>
