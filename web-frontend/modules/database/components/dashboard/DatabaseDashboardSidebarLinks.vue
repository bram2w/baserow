<template>
  <li>
    <nuxt-link
      :to="{ name: 'database-api-docs' }"
      class="dashboard__sidebar-link"
    >
      <i class="iconoir-book"></i>
      {{ $t('databaseDashboardSidebarLinks.apiDocumentation') }}
    </nuxt-link>
  </li>
</template>

<script>
export default {
  name: 'DatabaseDashboardSidebarLinks',
}
</script>
