<template>
  <div>
    <header class="layout-col-3-1 header">
      <ul class="header-filter">
        <li class="header-filter-item">
          <a
            ref="viewsSelectToggle"
            class="header-filter-link"
            @click="$refs.viewsContext.toggle($refs.viewsSelectToggle)"
          >
            <span v-if="hasSelectedView">
              <i
                class="header-filter-icon fas"
                :class="'fa-' + selectedView._.type.iconClass"
              ></i>
              {{ selectedView.name }}
            </span>
            <span v-if="!hasSelectedView">
              <i
                class="header-filter-icon header-filter-icon-no-choice fas fa-caret-square-down"
              ></i>
              Choose view
            </span>
          </a>
          <ViewsContext ref="viewsContext" :table="table"></ViewsContext>
        </li>
      </ul>
      <template v-if="hasSelectedView">
        <component
          :is="getViewHeaderComponent(selectedView)"
          :database="database"
          :table="table"
          :view="selectedView"
        />
      </template>
      <ul class="header-info">
        <li>{{ database.name }}</li>
        <li>{{ table.name }}</li>
      </ul>
    </header>
    <div class="layout-col-3-2 content">
      <template v-if="hasSelectedView">
        <component
          :is="getViewComponent(selectedView)"
          :database="database"
          :table="table"
          :view="selectedView"
        />
      </template>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

import ViewsContext from '@/modules/database/components/view/ViewsContext'

export default {
  layout: 'app',
  components: {
    ViewsContext
  },
  props: {
    databaseId: {
      type: Number,
      required: true
    },
    tableId: {
      type: Number,
      required: true
    }
  },
  computed: {
    ...mapState({
      selectedView: state => state.view.selected
    }),
    ...mapGetters({
      hasSelectedView: 'view/hasSelected'
    })
  },
  asyncData({ store, params, error, app }) {
    // @TODO figure out why the id's aren't converted to an int in the route.
    const databaseId = parseInt(params.databaseId)
    const tableId = parseInt(params.tableId)

    return store
      .dispatch('table/preSelect', { databaseId, tableId })
      .then(data => {
        return { database: data.database, table: data.table }
      })
      .catch(() => {
        return error({ statusCode: 404, message: 'Table not found.' })
      })
  },
  methods: {
    getViewComponent(view) {
      const type = this.$store.getters['view/getType'](view.type)
      return type.getComponent()
    },
    getViewHeaderComponent(view) {
      const type = this.$store.getters['view/getType'](view.type)
      return type.getHeaderComponent()
    }
  }
}
</script>
