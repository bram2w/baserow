<template>
  <nuxt-link :to="{ name: 'database-api-docs' }" class="dashboard__resource">
    <div class="dashboard__resource-inner">
      <span class="dashboard__resource-icon">
        <i class="iconoir-code"></i
      ></span>
      <div class="dashboard__resource-content">
        <h4 class="dashboard__resource-title">
          {{ $t('databaseDashboardResourceLinks.title') }}
        </h4>
        <p class="dashboard__resource-text">
          {{ $t('databaseDashboardResourceLinks.description') }}
        </p>
      </div>
    </div>
  </nuxt-link>
</template>

<script>
export default {
  name: 'DatabaseDashboardResourceLinks',
}
</script>
