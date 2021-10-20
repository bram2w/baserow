<template>
  <li
    v-tooltip="deactivated ? deactivatedText : null"
    class="tree__item"
    :class="{
      active: $route.matched.some(({ name }) => name === adminType.routeName),
    }"
  >
    <div
      class="tree__action sidebar__action"
      :class="{
        'tree__action--disabled': deactivated,
        'tree__action--deactivated': deactivated,
      }"
    >
      <nuxt-link
        :event="deactivated ? '' : 'click'"
        :to="{ name: adminType.routeName }"
        class="tree__link"
      >
        <i class="tree__icon fas" :class="'fa-' + adminType.iconClass"></i>
        <span class="sidebar__item-name">{{ adminType.getName() }}</span>
      </nuxt-link>
    </div>
  </li>
</template>

<script>
export default {
  name: 'SidebarAdminItem',
  props: {
    adminType: {
      required: true,
      type: Object,
    },
  },
  computed: {
    deactivatedText() {
      return this.$registry
        .get('admin', this.adminType.type)
        .getDeactivatedText()
    },
    deactivated() {
      return this.$registry.get('admin', this.adminType.type).isDeactivated()
    },
  },
}
</script>
