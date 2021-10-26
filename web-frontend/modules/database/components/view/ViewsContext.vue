<template>
  <Context ref="viewsContext" class="select" @shown="shown">
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
      ref="dropdown"
      v-auto-overflow-scroll
      class="select__items"
    >
      <ViewsContextItem
        v-for="view in searchAndOrder(views)"
        :ref="'view-' + view.id"
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
            @created="scrollViewDropdownToBottom()"
          ></CreateViewModal>
        </a>
      </div>
    </div>
  </Context>
</template>

<script>
import { mapState } from 'vuex'

import context from '@baserow/modules/core/mixins/context'
import dropdownHelpers from '@baserow/modules/core/mixins/dropdownHelpers'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ViewsContextItem from '@baserow/modules/database/components/view/ViewsContextItem'
import CreateViewModal from '@baserow/modules/database/components/view/CreateViewModal'
import { escapeRegExp } from '@baserow/modules/core/utils/string'

export default {
  name: 'ViewsContext',
  components: {
    ViewsContextItem,
    CreateViewModal,
  },
  mixins: [context, dropdownHelpers],
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
      firstShow: true,
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
    shown() {
      if (this.firstShow) {
        this.$nextTick(() => {
          this.scrollViewDropdownIfNeeded()
        })
        this.firstShow = false
      }
    },
    selectedView(view) {
      this.hide()
      this.$emit('selected-view', view)
    },
    /*
      If the currently selected view is not visible inside the dropdown we need to
      scroll just enough so that the selected view is visible as the last element
      in the dropdown.
      In case there are no views, we don't need to do anything and can simply return.
    */
    scrollViewDropdownIfNeeded() {
      if (this.views.length === 0) {
        return
      }
      const dropdownElement = this.$refs.dropdown
      const selectedViewItem = this.getSelectedViewItem()
      const dropdownHeight = dropdownElement.clientHeight
      if (
        this.isSelectedViewOutOfDropdownView(selectedViewItem, dropdownHeight)
      ) {
        dropdownElement.scrollTop = this.calculateOffsetToSelectedViewItem(
          dropdownElement,
          selectedViewItem
        )
      }
    },
    /**
     * This method scrolls the ViewDropdown to the bottom
     */
    scrollViewDropdownToBottom() {
      this.$refs.dropdown.scrollTop = this.$refs.dropdown.scrollHeight
    },
    /**
     * This method filters the view elements and returns the currently selected
     * view dom item based on whether or not it is selected.
     */
    getSelectedViewItem() {
      const selectedViewArray = this.views.filter((item) => item._.selected)
      const selectedViewItemID = selectedViewArray[0].id
      return this.$refs[`view-${selectedViewItemID}`][0].$el
    },
    /**
     * This method calculates whether or not the selectedViewItem is fully visible
     * inside the ViewContext dropdown or not
     */
    isSelectedViewOutOfDropdownView(selectedViewItem, dropdownHeight) {
      const selectedOffsetPlusHeight =
        selectedViewItem.offsetTop + selectedViewItem.clientHeight
      return selectedOffsetPlusHeight > dropdownHeight
    },
    /**
     * This method calculates the necessary offsetTop of the dropdown element so that
     * the selected view item is the bottom element.
     */
    calculateOffsetToSelectedViewItem(dropdownElement, selectedViewItem) {
      const {
        parentContainerBeforeHeight,
        itemHeightWithMargins,
        itemsInView,
      } = this.getStyleProperties(dropdownElement, selectedViewItem)

      const viewItemsBeforeSelectedViewItemHeight =
        (itemsInView - 1) * itemHeightWithMargins

      return (
        selectedViewItem.offsetTop -
        viewItemsBeforeSelectedViewItemHeight -
        parentContainerBeforeHeight
      )
    },
    toggleCreateViewModal(type) {
      const target = this.$refs['createViewModalToggle' + type][0]
      this.$refs['createViewModal' + type][0].toggle(target)
    },
    searchAndOrder(views) {
      const query = this.query

      return views
        .filter(function (view) {
          const regex = new RegExp('(' + escapeRegExp(query) + ')', 'i')
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
