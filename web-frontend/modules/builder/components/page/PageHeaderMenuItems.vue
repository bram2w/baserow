<template>
  <ul class="header__filter">
    <li
      v-for="(itemType, index) in pageHeaderItemTypes"
      :key="itemType.getType()"
      class="header__filter-item"
    >
      <a
        ref="button"
        class="header__filter-link"
        @click="itemType.onClick($refs.component[index], $refs.button[index])"
      >
        <i class="header__filter-icon fas" :class="`fa-${itemType.icon}`"></i>
        <span class="header__filter-name">{{ itemType.label }}</span>
      </a>
      <component :is="itemType.component" ref="component" :page="page" />
    </li>
  </ul>
</template>

<script>
export default {
  name: 'PageHeaderMenuItems',
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  computed: {
    pageHeaderItemTypes() {
      return Object.values(this.$registry.getAll('pageHeaderItem'))
    },
  },
}
</script>
