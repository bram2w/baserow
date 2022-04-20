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
  middleware: ['settings', 'authenticated', 'groupsAndApplications'],
  computed: {
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
      if (
        // Temporarily check if the undo redo is enabled.
        this.$featureFlags.includes('undo') &&
        osSpecificModifierPressed &&
        event.code === 'KeyZ' &&
        // If the active element is the body, it means that we're not focussing on
        // other (text) inputs that have their own undo action. This will prevent the
        // undo redo functionality while editing a cell directly.
        document.body === document.activeElement
      ) {
        event.shiftKey ? this.redo() : this.undo()
      }
    },
  },
}
</script>
