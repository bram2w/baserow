<template>
  <aside class="side-panels">
    <Tabs :key="element?.id" :full-height="true">
      <Tab
        v-for="pageSidePanelType in pageSidePanelTypes"
        :key="pageSidePanelType.getType()"
        :tooltip="
          element && pageSidePanelType.isDeactivated(element)
            ? pageSidePanelType.getDeactivatedText()
            : null
        "
        :title="pageSidePanelType.label"
        :disabled="!element || pageSidePanelType.isDeactivated(element)"
      >
        <component
          :is="pageSidePanelType.component"
          v-if="element"
          class="side-panels__panel"
        />
        <EmptySidePanelState v-else />
      </Tab>
    </Tabs>
  </aside>
</template>

<script>
import { mapGetters } from 'vuex'
import EmptySidePanelState from '@baserow/modules/builder/components/page/sidePanels/EmptySidePanelState'

export default {
  name: 'PageSidePanels',
  components: { EmptySidePanelState },
  computed: {
    ...mapGetters({
      element: 'element/getSelected',
    }),
    pageSidePanelTypes() {
      return this.$registry.getOrderedList('pageSidePanel')
    },
  },
}
</script>
