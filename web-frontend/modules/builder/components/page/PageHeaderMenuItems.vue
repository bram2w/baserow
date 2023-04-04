<template>
  <ul class="header__filter">
    <li
      v-for="(item, index) in pageHeaderItemTypes"
      :key="item.getType()"
      class="header__filter-item"
    >
      <a
        ref="button"
        class="header__filter-link"
        @click="item.onClick($refs.component[index], $refs.button[index])"
      >
        <i class="header__filter-icon fas" :class="`fa-${item.icon}`"></i>
        <span class="header__filter-name">{{ item.label }}</span>
      </a>
      <component :is="item.component" ref="component" />
    </li>
  </ul>
</template>

<script>
export default {
  name: 'PageHeaderMenuItems',
  computed: {
    pageHeaderItemTypes() {
      return Object.values(this.$registry.getAll('pageHeaderItem'))
    },
  },
}
</script>
