<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        'active--warning': view.sortings.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-sort"></i>
      Sort
    </a>
    <ViewSortContext
      ref="context"
      :view="view"
      :fields="fields"
      :primary="primary"
      @changed="$emit('changed')"
    ></ViewSortContext>
  </div>
</template>

<script>
import ViewSortContext from './ViewSortContext'

export default {
  name: 'ViewSort',
  components: { ViewSortContext },
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
}
</script>
