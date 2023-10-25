<template>
  <div v-if="databases.length > 0">
    <div class="select-application__group">{{ workspace.name }}</div>
    <ul class="select-application__list">
      <li v-for="database in databases" :key="database.id">
        <nuxt-link
          :to="{
            name: 'database-api-docs-detail',
            params: {
              databaseId: database.id,
            },
          }"
          class="select-application__link"
          :class="{ active: selected === database.id }"
        >
          <div class="select-application__icon">
            <i :class="database._.type.iconClass"></i>
          </div>
          <div class="select-application__name">
            {{ database.name }}
          </div>
        </nuxt-link>
      </li>
    </ul>
  </div>
</template>

<script>
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export default {
  name: 'APIDocsSelectDatabaseWorkspace',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    selected: {
      type: Number,
      required: false,
      default: -1,
    },
  },
  computed: {
    databases() {
      const applications = this.$store.getters['application/getAllOfWorkspace'](
        this.workspace
      )
      const databaseType = DatabaseApplicationType.getType()
      return applications.filter(
        (application) => application.type === databaseType
      )
    },
  },
}
</script>
