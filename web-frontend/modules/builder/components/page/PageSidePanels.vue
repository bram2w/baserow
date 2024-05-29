<template>
  <aside class="side-panels">
    <Tabs :key="element?.id" full-height>
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
        <ReadOnlyForm
          v-if="element"
          :read-only="
            !$hasPermission(
              'builder.page.element.update',
              element,
              workspace.id
            )
          "
        >
          <component
            :is="pageSidePanelType.component"
            class="side-panels__panel"
          />
        </ReadOnlyForm>
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
  inject: ['workspace'],
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
