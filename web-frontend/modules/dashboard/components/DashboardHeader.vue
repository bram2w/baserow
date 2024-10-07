<template>
  <header class="layout__col-2-1 header header--space-between">
    <DashboardHeaderMenuItems :dashboard="dashboard" />
    <div>
      <!-- Add new... button -->
    </div>
  </header>
</template>

<script>
import DashboardHeaderMenuItems from '@baserow/modules/dashboard/components/DashboardHeaderMenuItems'

export default {
  name: 'DashboardHeader',
  components: {
    DashboardHeaderMenuItems,
  },
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
  },
}
</script>
