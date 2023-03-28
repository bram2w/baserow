<template>
  <Tabs :full-height="true" :navigation="true" :large="true">
    <tab
      v-for="page in pages"
      :key="page.type"
      :title="page.name"
      :disabled="!page.navigable"
      :to="page.to"
      :tooltip="!page.navigable ? $t('enterprise.deactivated') : null"
    >
      <NuxtChild :workspace="workspace" />
    </tab>
  </Tabs>
</template>

<script>
export default {
  name: 'Settings',
  layout: 'app',
  async asyncData({ store, params, error }) {
    try {
      const workspace = await store.dispatch(
        'workspace/selectById',
        parseInt(params.workspaceId, 10)
      )
      return { workspace }
    } catch (e) {
      return error({ statusCode: 404, message: 'Workspace not found.' })
    }
  },
  computed: {
    workspaceSettingsPageTypes() {
      return Object.values(this.$registry.getAll('workspaceSettingsPage'))
    },
    pages() {
      // Build an array of settings page types they're permitted to view.
      const permittedPages = this.workspaceSettingsPageTypes.filter(
        (instance) => instance.hasPermission(this.workspace)
      )
      return permittedPages.map((instance) => {
        return {
          type: instance.type,
          name: instance.getName(),
          to: instance.getRoute(this.workspace),
          navigable: instance.isFeatureActive(this.workspace),
        }
      })
    },
  },
  mounted() {
    this.$bus.$on('workspace-deleted', this.workspaceDeleted)
  },
  beforeDestroy() {
    this.$bus.$off('workspace-deleted', this.workspaceDeleted)
  },
  methods: {
    workspaceDeleted() {
      this.$nuxt.$router.push({ name: 'dashboard' })
    },
  },
}
</script>
