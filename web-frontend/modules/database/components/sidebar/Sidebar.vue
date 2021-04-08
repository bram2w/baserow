<template>
  <SidebarApplication :application="application" @selected="selected">
    <template #context>
      <li>
        <nuxt-link
          :to="{
            name: 'database-api-docs-detail',
            params: {
              databaseId: application.id,
            },
          }"
        >
          <i class="context__menu-icon fas fa-fw fa-book"></i>
          View API docs
        </nuxt-link>
      </li>
    </template>
    <template v-if="application._.selected" #body>
      <ul class="tree__subs">
        <SidebarItem
          v-for="table in application.tables"
          :key="table.id"
          :database="application"
          :table="table"
        ></SidebarItem>
      </ul>
      <a class="tree__sub-add" @click="$refs.createTableModal.show()">
        <i class="fas fa-plus"></i>
        Create table
      </a>
      <CreateTableModal
        ref="createTableModal"
        :application="application"
      ></CreateTableModal>
    </template>
  </SidebarApplication>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import SidebarItem from '@baserow/modules/database/components/sidebar/SidebarItem'
import CreateTableModal from '@baserow/modules/database/components/table/CreateTableModal'
import SidebarApplication from '@baserow/modules/core/components/sidebar/SidebarApplication'

export default {
  name: 'Sidebar',
  components: { SidebarApplication, SidebarItem, CreateTableModal },
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  methods: {
    async selected(application) {
      try {
        await this.$store.dispatch('application/select', application)
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
