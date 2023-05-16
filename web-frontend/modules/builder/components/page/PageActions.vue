<template>
  <ul class="header__filter">
    <li
      v-for="(actionType, index) in pageActionTypes"
      :key="actionType.getType()"
      class="header__filter-item header__filter-item--right"
    >
      <a
        ref="button"
        class="header__filter-link"
        @click="
          actionType.onClick({
            component: $refs.component[index],
            button: $refs.button[index],
            builder: builder,
            page: page,
          })
        "
      >
        <i
          v-if="actionType.icon"
          class="header__filter-icon fas"
          :class="`fa-${actionType.icon}`"
        ></i>
        <span class="header__filter-name">{{ actionType.label }}</span>
      </a>
      <component
        :is="actionType.component"
        ref="component"
        :builder="builder"
        :page="page"
      />
    </li>
  </ul>
</template>

<script>
export default {
  name: 'PageActions',
  inject: ['builder'],
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  computed: {
    pageActionTypes() {
      return Object.values(this.$registry.getOrderedList('pageAction'))
    },
  },
}
</script>
