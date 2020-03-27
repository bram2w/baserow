<template>
  <div>
    <ul class="tree-subs">
      <SidebarItem
        v-for="table in application.tables"
        :key="table.id"
        :database="application"
        :table="table"
      ></SidebarItem>
    </ul>
    <a class="tree-sub-add" @click="$refs.createTableModal.show()">
      <i class="fas fa-plus"></i>
      Create table
    </a>
    <CreateTableModal
      ref="createTableModal"
      :application="application"
    ></CreateTableModal>
  </div>
</template>

<script>
import SidebarItem from '@baserow/modules/database/components/table/SidebarItem'
import CreateTableModal from '@baserow/modules/database/components/table/CreateTableModal'

export default {
  name: 'Sidebar',
  components: { SidebarItem, CreateTableModal },
  props: {
    application: {
      type: Object,
      required: true
    }
  }
}
</script>
