<template>
  <li>
    <nuxt-link
      :to="{ name: 'database-api-docs' }"
      class="dashboard__sidebar-link"
    >
      <i class="dashboard__sidebar-link-icon iconoir-book"></i>
      <span class="dashboard__sidebar-link-text">{{
        $t('databaseDashboardSidebarLinks.apiDocumentation')
      }}</span>
    </nuxt-link>
  </li>
</template>

<script>
export default {
  name: 'DatabaseDashboardSidebarLinks',
}
</script>
