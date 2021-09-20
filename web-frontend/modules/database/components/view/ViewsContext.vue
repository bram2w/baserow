<template>
  <Context ref="viewsContext" class="select">
    <div class="select__search">
      <i class="select__search-icon fas fa-search"></i>
      <input
        v-model="query"
        type="text"
        class="select__search-input"
        :placeholder="$t('viewsContext.searchView')"
      />
    </div>
    <div v-if="isLoading" class="context--loading">
      <div class="loading"></div>
    </div>
    <ul
      v-if="!isLoading && views.length > 0"
      v-auto-overflow-scroll
      class="select__items"
    >
      <ViewsContextItem
        v-for="view in searchAndOrder(views)"
        :key="view.id"
        v-sortable="{ id: view.id, update: order, marginTop: -1.5 }"
        :view="view"
        :table="table"
        :read-only="readOnly"
        @selected="selectedView"
      ></ViewsContextItem>
    </ul>
    <div v-if="!isLoading && views.length == 0" class="context__description">
      {{ $t('viewsContext.noViews') }}
    </div>
    <div v-if="!readOnly" class="select__footer">
      <div class="select__footer-multiple">
        <div class="select__footer-multiple-label">
          {{ $t('viewsContext.addView') }}
        </div>
        <a
          v-for="(viewType, type) in viewTypes"
          :key="type"
          :ref="'createViewModalToggle' + type"
          class="select__footer-multiple-item"
          @click="toggleCreateViewModal(type)"
        >
          <i
            class="select__footer-multiple-icon fas"
            :class="'fa-' + viewType.iconClass"
          ></i>
          {{ viewType.getName() }}
          <CreateViewModal
            :ref="'createViewModal' + type"
            :table="table"
            :view-type="viewType"
          ></CreateViewModal>
        </a>
      </div>
    </div>
  </Context>
</template>

<script>
import { mapState } from 'vuex'

import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ViewsContextItem from '@baserow/modules/database/components/view/ViewsContextItem'
import CreateViewModal from '@baserow/modules/database/components/view/CreateViewModal'

export default {
  name: 'ViewsContext',
  components: {
    ViewsContextItem,
    CreateViewModal,
  },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true,
    },
    views: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      query: '',
    }
  },
  computed: {
    viewTypes() {
      return this.$registry.getAll('view')
    },
    ...mapState({
      isLoading: (state) => state.view.loading,
      isLoaded: (state) => state.view.loaded,
    }),
  },
  methods: {
    selectedView(view) {
      this.hide()
      this.$emit('selected-view', view)
    },
    toggleCreateViewModal(type) {
      const target = this.$refs['createViewModalToggle' + type][0]
      this.$refs['createViewModal' + type][0].toggle(target)
    },
    searchAndOrder(views) {
      const query = this.query

      return views
        .filter(function (view) {
          const regex = new RegExp('(' + query + ')', 'i')
          return view.name.match(regex)
        })
        .sort((a, b) => a.order - b.order)
    },
    async order(order, oldOrder) {
      try {
        await this.$store.dispatch('view/order', {
          table: this.table,
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "viewsContext": {
      "searchView": "Search views",
      "noViews": "No views found",
      "addView": "Add a view:"
    }
  },
  "fr": {
    "viewsContext": {
      "searchView": "Recherche",
      "noViews": "Aucune vue trouvée",
      "addView": "Ajouter une vue:"
    }
  }
}
</i18n>
