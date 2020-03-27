<template>
  <Context ref="viewsContext" class="select">
    <div class="select-search">
      <i class="select-search-icon fas fa-search"></i>
      <input
        v-model="query"
        type="text"
        class="select-search-input"
        placeholder="Search views"
      />
    </div>
    <div v-if="isLoading" class="context-loading">
      <div class="loading"></div>
    </div>
    <ul v-if="!isLoading && isLoaded && views.length > 0" class="select-items">
      <ViewsContextItem
        v-for="view in search(views)"
        :key="view.id"
        :view="view"
        @selected="hide"
      ></ViewsContextItem>
    </ul>
    <div
      v-if="!isLoading && isLoaded && views.length == 0"
      class="context-description"
    >
      No views found
    </div>
    <div class="select-footer">
      <div class="select-footer-multiple">
        <div class="select-footer-multiple-label">Add a view:</div>
        <a
          v-for="(viewType, type) in viewTypes"
          :key="type"
          :ref="'createViewModalToggle' + type"
          class="select-footer-multiple-item"
          @click="toggleCreateViewModal(type)"
        >
          <i
            class="select-footer-multiple-icon fas"
            :class="'fa-' + viewType.iconClass"
          ></i>
          {{ viewType.name }}
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
import ViewsContextItem from '@baserow/modules/database/components/view/ViewsContextItem'
import CreateViewModal from '@baserow/modules/database/components/view/CreateViewModal'

export default {
  name: 'ViewsContext',
  components: {
    ViewsContextItem,
    CreateViewModal
  },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      query: ''
    }
  },
  computed: {
    ...mapState({
      isLoading: state => state.view.loading,
      isLoaded: state => state.view.loaded,
      viewTypes: state => state.view.types,
      views: state => state.view.items
    })
  },
  methods: {
    toggleCreateViewModal(type) {
      const target = this.$refs['createViewModalToggle' + type][0]
      this.$refs['createViewModal' + type][0].toggle(target)
    },
    search(views) {
      const query = this.query

      return views.filter(function(view) {
        const regex = new RegExp('(' + query + ')', 'i')
        return view.name.match(regex)
      })
    }
  }
}
</script>
