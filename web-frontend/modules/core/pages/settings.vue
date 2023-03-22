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
      <NuxtChild :group="group" />
    </tab>
  </Tabs>
</template>

<script>
export default {
  name: 'Settings',
  layout: 'app',
  async asyncData({ store, params, error }) {
    try {
      const group = await store.dispatch(
        'group/selectById',
        parseInt(params.groupId, 10)
      )
      return { group }
    } catch (e) {
      return error({ statusCode: 404, message: 'Group not found.' })
    }
  },
  computed: {
    groupSettingsPageTypes() {
      return Object.values(this.$registry.getAll('groupSettingsPage'))
    },
    pages() {
      // Build an array of settings page types they're permitted to view.
      const permittedPages = this.groupSettingsPageTypes.filter((instance) =>
        instance.hasPermission(this.group)
      )
      return permittedPages.map((instance) => {
        return {
          type: instance.type,
          name: instance.getName(),
          to: instance.getRoute(this.group),
          navigable: instance.isFeatureActive(this.group),
        }
      })
    },
  },
  mounted() {
    this.$bus.$on('group-deleted', this.groupDeleted)
  },
  beforeDestroy() {
    this.$bus.$off('group-deleted', this.groupDeleted)
  },
  methods: {
    groupDeleted() {
      this.$nuxt.$router.push({ name: 'dashboard' })
    },
  },
}
</script>
