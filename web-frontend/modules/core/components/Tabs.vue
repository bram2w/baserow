<template lang="html">
  <div>
    <ul class="tabs">
      <li
        v-for="(tab, index) in tabs"
        :key="tab.title"
        class="tabs__item"
        :class="{
          'tabs__item--active': index == internalSelectedIndex,
          'tabs__item--disabled': tab.disabled,
        }"
        @click="tab.disabled ? null : selectTab(index)"
      >
        <a class="tabs__link" :class="{ 'tabs__link--disabled': tab.disabled }">
          {{ tab.title }}
        </a>
      </li>
    </ul>
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'Tabs',
  props: {
    selectedIndex: {
      type: Number,
      required: false,
      default: 0,
    },
  },
  data() {
    return {
      internalSelectedIndex: 0, // In case the prop isn't used by a parent
      tabs: [], // all the tabs
    }
  },
  watch: {
    selectedIndex: {
      handler(i) {
        if (i !== undefined) {
          this.internalSelectedIndex = i
        }
      },
      immediate: true,
    },
  },
  created() {
    this.tabs = this.$children
  },
  mounted() {
    this.selectTab(this.internalSelectedIndex)
  },
  methods: {
    selectTab(i) {
      this.$emit('update:selected-index', i)
      this.internalSelectedIndex = i

      this.tabs.forEach((tab, index) => {
        tab.isActive = index === i
      })
    },
  },
}
</script>
