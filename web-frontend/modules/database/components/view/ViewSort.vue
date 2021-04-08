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
      {{ sortTitle }}
    </a>
    <ViewSortContext
      ref="context"
      :view="view"
      :fields="fields"
      :primary="primary"
      :read-only="readOnly"
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
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    sortTitle() {
      const numberOfSortings = this.view.sortings.length
      if (numberOfSortings === 0) {
        return 'Sort'
      } else if (numberOfSortings === 1) {
        return `${numberOfSortings} Sort`
      } else {
        return `${numberOfSortings} Sorts`
      }
    },
  },
}
</script>
