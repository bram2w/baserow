<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        active: view.filters.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-filter"></i>
      Filter
    </a>
    <ViewFilterContext
      ref="context"
      :view="view"
      :fields="fields"
      :primary="primary"
      @changed="$emit('changed')"
    ></ViewFilterContext>
  </div>
</template>

<script>
import ViewFilterContext from '@baserow/modules/database/components/view/ViewFilterContext'

export default {
  name: 'ViewFilter',
  components: { ViewFilterContext },
  props: {
    primary: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
  },
  beforeMount() {
    this.$bus.$on('view-filter-created', this.filterCreated)
  },
  beforeDestroy() {
    this.$bus.$off('view-filter-created', this.filterCreated)
  },
  methods: {
    /**
     * When a filter is created via an outside source we want to show the context menu.
     */
    filterCreated() {
      this.$refs.context.show(this.$refs.contextLink, 'bottom', 'left', 4)
    },
  },
}
</script>
