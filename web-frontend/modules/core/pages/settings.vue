<template>
  <div>
    <div class="layout__col-2-1">
      <ul class="page-tabs">
        <nuxt-link
          v-for="page in pages"
          :key="page.type"
          v-slot="{ href, navigate, isExactActive }"
          :to="page.to"
        >
          <li
            v-tooltip="!page.navigable ? $t('enterprise.deactivated') : null"
            class="page-tabs__item"
            :class="{
              'page-tabs__item--active': isExactActive,
              'page-tabs__item--disabled': !page.navigable,
            }"
          >
            <a
              :href="page.navigable ? href : null"
              class="page-tabs__link"
              v-on="page.navigable ? { click: navigate } : {}"
            >
              {{ page.name }}
            </a>
          </li>
        </nuxt-link>
      </ul>
    </div>
    <div class="layout__col-2-2">
      <NuxtChild :group="group" />
    </div>
  </div>
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
