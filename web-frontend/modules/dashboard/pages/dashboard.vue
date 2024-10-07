<template>
  <div class="dashboard-app">
    <DashboardHeader :dashboard="dashboard" />
    <div class="layout__col-2-2 dashboard-app__content">
      <div class="dashboard-app__content-header">
        <div class="dashboard-app__title">{{ dashboard.name }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import DashboardHeader from '@baserow/modules/dashboard/components/DashboardHeader'

export default {
  name: 'Dashboard',
  components: { DashboardHeader },
  layout: 'app',
  async asyncData({ store, params, error, $registry }) {
    const dashboardId = parseInt(params.dashboardId)
    const data = {}
    try {
      const dashboard = await store.dispatch(
        'application/selectById',
        dashboardId
      )
      const workspace = await store.dispatch(
        'workspace/selectById',
        dashboard.workspace.id
      )
      data.workspace = workspace
      data.dashboard = dashboard
    } catch (e) {
      return error({ statusCode: 404, message: 'Dashboard not found.' })
    }
    return data
  },
}
</script>
