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
      <span class="header__filter-name">{{
        $tc('viewSort.sort', view.sortings.length, {
          count: view.sortings.length,
        })
      }}</span>
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
}
</script>

<i18n>
{
  "en":{
    "viewSort":{
      "sort": "Sort | 1 Sort | {count} Sorts"
    }
  },
  "fr":{
    "viewSort":{
      "sort": "Tri | 1 Tri | {count} Tris"
    }
  }
}
</i18n>
