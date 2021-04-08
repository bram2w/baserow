<template>
  <ul v-if="!tableLoading" class="header__filter header__filter--full-width">
    <li class="header__filter-item">
      <GridViewHide :view="view" :fields="fields"></GridViewHide>
    </li>
    <li class="header__filter-item header__filter-item--right">
      <ViewSearch :view="view" @refresh="$emit('refresh', $event)"></ViewSearch>
    </li>
  </ul>
</template>

<script>
import { mapState } from 'vuex'

import GridViewHide from '@baserow/modules/database/components/view/grid/GridViewHide'
import ViewSearch from '@baserow/modules/database/components/view/ViewSearch'

export default {
  name: 'GridViewHeader',
  components: { GridViewHide, ViewSearch },
  props: {
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapState({
      tableLoading: (state) => state.table.loading,
    }),
  },
}
</script>
