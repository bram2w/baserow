<template>
  <div
    :class="{
      'onboarding-tool-preview': true,
      'onboarding-tool-preview__focus-table': focusOnTable,
    }"
  >
    <div ref="inner" class="onboarding-tool-preview__inner">
      <div
        class="onboarding-tool-preview__highlight"
        :class="{
          'onboarding-tool-preview__highlight--hidden':
            highlightPosition.width === 0 && highlightPosition.height === 0,
        }"
        :style="{
          left: `${highlightPosition.left}px`,
          top: `${highlightPosition.top}px`,
          width: `${highlightPosition.width}px`,
          height: `${highlightPosition.height}px`,
        }"
      ></div>
      <div class="layout">
        <div class="layout__col-1">
          <Sidebar
            ref="sidebar"
            :workspaces="workspaces"
            :selected-workspace="selectedWorkspace"
            :applications="applications"
          ></Sidebar>
        </div>
        <div class="layout__col-2">
          <component
            :is="col2Component"
            v-if="col2Component"
            :data="data"
            :selected-workspace="selectedWorkspace"
            :applications="applications"
            @focusOnTable="handleFocusOnTable"
          ></component>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'
import { populateWorkspace } from '@baserow/modules/core/store/workspace'
import { populateApplication } from '@baserow/modules/core/store/application'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import { WorkspaceOnboardingType } from '@baserow/modules/core/onboardingTypes'
import { clone } from '@baserow/modules/core/utils/object'

export default {
  name: 'AppLayoutPreview',
  components: { Sidebar },
  props: {
    data: {
      type: Object,
      required: true,
    },
    highlightDataName: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {
      focusOnTable: false,
      highlightPosition: {
        visible: false,
        left: 0,
        top: 0,
        width: 0,
        height: 0,
      },
    }
  },
  computed: {
    selectedWorkspace() {
      const workspace = populateWorkspace({
        id: 0,
        name: this.data[WorkspaceOnboardingType.getType()]?.name || '',
        users: [],
      })
      workspace._.is_onboarding = true
      return workspace
    },
    workspaces() {
      return [this.selectedWorkspace]
    },
    applications() {
      const baseApplication = populateApplication(
        {
          id: 0,
          name: '',
          order: 1,
          type: DatabaseApplicationType.getType(),
          workspace: this.selectedWorkspace,
          tables: [],
        },

        this.$registry
      )
      const application = clone(baseApplication)
      application.name = ''
      const application2 = clone(baseApplication)
      application2.id = -1
      const application3 = clone(baseApplication)
      application3.id = -2
      return [application, application2, application3]
    },
    col2Component() {
      return null
    },
  },
  watch: {
    highlightDataName() {
      this.updateHighlightedElement()
    },
  },
  mounted() {
    this.resizeObserver = new ResizeObserver(() => {
      this.updateHighlightedElement()
    })
    this.resizeObserver.observe(this.$el)
    this.updateHighlightedElement()
  },
  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el)
  },
  methods: {
    updateHighlightedElement() {
      const position = {
        left: 0,
        top: 0,
        width: 0,
        height: 0,
      }

      if (this.highlightDataName !== '') {
        const element = this.$el.querySelector(
          `[data-highlight='${this.highlightDataName}']`
        )
        if (element) {
          const parentRect = this.$refs.inner.getBoundingClientRect()
          const elementRect = element.getBoundingClientRect()
          const padding = 2
          position.top = elementRect.top - parentRect.top - padding
          position.left = elementRect.left - parentRect.left - padding
          position.width = elementRect.width + padding * 2
          position.height = elementRect.height + padding * 2
        }
      }

      this.highlightPosition = position
    },
    handleFocusOnTable(focusOnTable) {
      this.focusOnTable = focusOnTable
    },
  },
}
</script>
