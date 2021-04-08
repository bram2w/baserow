<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        'active--primary': headerSearchTerm.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 4)"
    >
      <i class="header__search-icon fas fa-search"></i>
      {{ headerSearchTerm }}
    </a>
    <ViewSearchContext
      ref="context"
      :view="view"
      :fields="fields"
      :primary="primary"
      :store-prefix="storePrefix"
      @refresh="$emit('refresh', $event)"
      @search-changed="searchChanged"
    ></ViewSearchContext>
  </div>
</template>

<script>
import ViewSearchContext from '@baserow/modules/database/components/view/ViewSearchContext'

export default {
  name: 'ViewSearch',
  components: { ViewSearchContext },
  props: {
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data: () => {
    return {
      headerSearchTerm: '',
    }
  },
  methods: {
    searchChanged(newSearch) {
      this.headerSearchTerm = newSearch
    },
  },
}
</script>
