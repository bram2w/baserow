<template lang="html">
  <div>
    <ul class="tabs">
      <li
        v-for="(tab, index) in tabs"
        :key="tab.title"
        class="tabs__item"
        :class="{ 'tabs__item--active': index == selectedIndex }"
        @click="selectTab(index)"
      >
        <a href="#" class="tabs__link">
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
  data() {
    return {
      selectedIndex: 0, // the index of the selected tab,
      tabs: [], // all of the tabs
    }
  },
  created() {
    this.tabs = this.$children
  },
  mounted() {
    this.selectTab(0)
  },
  methods: {
    selectTab(i) {
      this.selectedIndex = i

      this.tabs.forEach((tab, index) => {
        tab.isActive = index === i
      })
    },
  },
}
</script>
