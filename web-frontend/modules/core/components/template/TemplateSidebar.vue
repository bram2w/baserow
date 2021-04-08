<template>
  <div class="sidebar">
    <div class="sidebar__nav">
      <ul class="tree">
        <li class="tree__item margin-top-2">
          <div class="tree__link tree__link--group">
            {{ template.name }}
          </div>
        </li>
        <component
          :is="getApplicationComponent(application)"
          v-for="application in applications"
          :key="application.id"
          :application="application"
          :page="page"
          @selected="selectedApplication"
          @selected-page="$emit('selected-page', $event)"
        ></component>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TemplateSidebar',
  props: {
    template: {
      type: Object,
      required: true,
    },
    applications: {
      type: Array,
      required: true,
    },
    page: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  methods: {
    getApplicationComponent(application) {
      return this.$registry
        .get('application', application.type)
        .getTemplateSidebarComponent()
    },
    selectedApplication(application) {
      this.applications.forEach((app) => {
        app._.selected = application.id === app.id
      })
    },
  },
}
</script>
