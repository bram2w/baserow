<template>
  <div class="dashboard-app">
    <DashboardHeader :dashboard="dashboard" />
    <div class="layout__col-2-2 dashboard-app__content">
      <div class="dashboard-app__content-header">
        <div class="dashboard-app__title">
          <Editable
            ref="dashboardNameEditable"
            :value="dashboard.name"
            @change="renameApplication(dashboard, $event)"
            @editing="editingDashboardName = $event"
          ></Editable>
          <a
            v-if="isEditMode"
            class="dashboard-app__edit"
            :class="{ 'visibility-hidden': editingDashboardName }"
            @click="editName"
          >
            <i class="dashboard-app__edit-icon iconoir-edit-pencil"></i
          ></a>
        </div>
        <div
          v-if="isEditMode || dashboard.description"
          class="dashboard-app__description"
        >
          <Editable
            ref="dashboardDescriptionEditable"
            :value="dashboard.description"
            :placeholder="$t('dashboard.descriptionPlaceholder')"
            @change="updateDescription(dashboard, $event)"
            @editing="editingDashboardDescription = $event"
          ></Editable>
          <a
            v-if="isEditMode"
            class="dashboard-app__edit"
            :class="{ 'visibility-hidden': editingDashboardDescription }"
            @click="editDescription"
          >
            <i class="dashboard-app__edit-icon iconoir-edit-pencil"></i
          ></a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import DashboardHeader from '@baserow/modules/dashboard/components/DashboardHeader'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { mapGetters } from 'vuex'

export default {
  name: 'Dashboard',
  components: { DashboardHeader },
  beforeRouteUpdate(to, from, next) {
    if (from.params.dashboardId !== to.params?.dashboardId) {
      this.$store.dispatch('dashboardApplication/reset')
    }
    next()
  },
  beforeRouteLeave(to, from, next) {
    this.$store.dispatch('dashboardApplication/reset')
    this.$store.dispatch('application/unselect')
    next()
  },
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
  data() {
    return {
      editingDashboardName: false,
      editingDashboardDescription: false,
    }
  },
  computed: {
    ...mapGetters({
      isEditMode: 'dashboardApplication/isEditMode',
    }),
  },
  methods: {
    editName() {
      this.$refs.dashboardNameEditable.edit()
      this.editingDashboardName = true
    },
    editDescription() {
      this.$refs.dashboardDescriptionEditable.edit()
      this.editingDashboardDescription = true
    },
    async renameApplication(application, event) {
      try {
        await this.$store.dispatch('application/update', {
          application,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.dashboardNameEditable.set(event.oldValue)
        notifyIf(error, 'application')
      } finally {
        this.editingDashboardName = false
      }
    },
    async updateDescription(application, event) {
      try {
        await this.$store.dispatch('application/update', {
          application,
          values: {
            description: event.value,
          },
        })
      } catch (error) {
        this.$refs.dashboardDescriptionEditable.set(event.oldValue)
        notifyIf(error, 'application')
      } finally {
        this.editingDashboardDescription = false
      }
    },
  },
}
</script>
