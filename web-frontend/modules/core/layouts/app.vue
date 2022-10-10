<template>
  <div>
    <Notifications></Notifications>
    <div :class="{ 'layout--collapsed': isCollapsed }" class="layout">
      <div class="layout__col-1">
        <Sidebar></Sidebar>
      </div>
      <div class="layout__col-2">
        <nuxt />
      </div>
      <component
        :is="component"
        v-for="(component, index) in appLayoutComponents"
        :key="index"
      ></component>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'
import undoRedo from '@baserow/modules/core/mixins/undoRedo'
import { CORE_ACTION_SCOPES } from '@baserow/modules/core/utils/undoRedoConstants'

export default {
  components: {
    Notifications,
    Sidebar,
  },
  mixins: [undoRedo],
  middleware: [
    'settings',
    'authenticated',
    'groupsAndApplications',
    'pendingJobs',
  ],
  computed: {
    appLayoutComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getAppLayoutComponent())
        .filter((component) => component !== null)
    },
    ...mapGetters({
      isCollapsed: 'sidebar/isCollapsed',
    }),
  },
  mounted() {
    // Connect to the web socket so we can start receiving real time updates.
    this.$realtime.connect()
    this.$el.keydownEvent = (event) => this.keyDown(event)
    document.body.addEventListener('keydown', this.$el.keydownEvent)
    this.$store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      CORE_ACTION_SCOPES.root()
    )
    this.$store.dispatch('job/initializePoller')
  },
  beforeDestroy() {
    this.$realtime.disconnect()
    document.body.removeEventListener('keydown', this.$el.keydownEvent)
    this.$store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      CORE_ACTION_SCOPES.root(false)
    )
  },
  methods: {
    keyDown(event) {
      const isMac = navigator.platform.toUpperCase().includes('MAC')
      const osSpecificModifierPressed = isMac ? event.metaKey : event.ctrlKey
      if (osSpecificModifierPressed && event.key.toLowerCase() === 'z') {
        // input/textareas/selects/editable dom elements have their own browser
        // controlled undo/redo functionality so don't use our own if they have the
        // focus.
        if (
          !['input', 'textarea', 'select'].includes(
            document.activeElement.tagName.toLowerCase()
          ) &&
          !document.activeElement.isContentEditable
        ) {
          event.shiftKey ? this.redo() : this.undo()
        }
      }
    },
  },
}
</script>
