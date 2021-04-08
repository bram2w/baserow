<template>
  <div class="templates__body">
    <template v-if="template !== null">
      <div v-if="loading" class="loading-absolute-center"></div>
      <div v-else class="layout">
        <div class="layout__col-1">
          <TemplateSidebar
            :template="template"
            :applications="applications"
            :page="page"
            @selected-page="selectPage"
          ></TemplateSidebar>
        </div>
        <div class="layout__col-2">
          <component
            :is="pageComponent"
            v-if="page !== null"
            :page-value="page.value"
          ></component>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import ApplicationService from '@baserow/modules/core/services/application'
import { populateApplication } from '@baserow/modules/core/store/application'
import TemplateSidebar from '@baserow/modules/core/components/template/TemplateSidebar'

export default {
  name: 'TemplateBody',
  components: { TemplateSidebar },
  props: {
    template: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  data() {
    return {
      loading: false,
      applications: [],
      page: null,
    }
  },
  computed: {
    pageComponent() {
      if (this.page !== null) {
        return this.$registry
          .get('application', this.page.application)
          .getTemplatesPageComponent()
      }
      return null
    },
  },
  watch: {
    template(value) {
      if (value === null) {
        this.loading = false
        this.applications = []
        this.page = null
        return
      }
      this.fetchApplications(value)
    },
  },
  methods: {
    async fetchApplications(template) {
      this.loading = true

      try {
        const { data } = await ApplicationService(this.$client).fetchAll(
          template.group_id
        )
        data.forEach((application) => {
          populateApplication(application, this.$registry)
        })
        this.applications = data

        // Check if there is an application that can give us an initial page. The
        // database application type would for example return the first table as page.
        for (let i = 0; i < this.applications.length; i++) {
          const application = this.applications[i]
          const pageValue = this.$registry
            .get('application', application.type)
            .getTemplatePage(application)
          if (pageValue !== null) {
            application._.selected = true
            this.selectPage({
              application: application.type,
              value: pageValue,
            })
            break
          }
        }
      } catch (error) {
        this.applications = []
        notifyIf(error, 'templates')
      } finally {
        this.loading = false
      }
    },
    selectPage({ application, value }) {
      this.page = { application, value }
    },
  },
}
</script>
