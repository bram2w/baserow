<template>
  <aside class="side-panels">
    <Tabs :full-height="true">
      <Tab
        v-for="pageSidePanelType in pageSidePanelTypes"
        :key="pageSidePanelType.label"
        :title="pageSidePanelType.label"
      >
        <component :is="pageSidePanelType.component" />
      </Tab>
    </Tabs>
  </aside>
</template>

<script>
export default {
  name: 'PageSidePanels',
  computed: {
    pageSidePanelTypes() {
      return this.$registry.getOrderedList('pageSidePanel')
    },
  },
}
</script>
