<template>
  <div
    class="tabs"
    :class="{
      'tabs--full-height': fullHeight,
      'tabs--no-separation': noSeparation,
      'tabs--large': large,
    }"
  >
    <ul class="tabs__header">
      <li
        v-for="(tab, index) in tabs"
        :key="tab.title"
        v-tooltip="tab.tooltip"
        class="tabs__item"
        :class="{
          'tabs__item--active': isActive(index),
          'tabs__item--disabled': tab.disabled,
        }"
        @click="tab.disabled ? null : selectTab(index)"
      >
        <a
          :href="getHref(index)"
          class="tabs__link"
          :class="{ 'tabs__link--disabled': tab.disabled }"
          @click.prevent=""
        >
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
    fullHeight: {
      type: Boolean,
      required: false,
      default: false,
    },
    noSeparation: {
      type: Boolean,
      required: false,
      default: false,
    },
    navigation: {
      type: Boolean,
      required: false,
      default: false,
    },
    large: {
      type: Boolean,
      required: false,
      default: false,
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
        if (!this.navigation && i !== undefined) {
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
    if (this.navigation) {
      this.tabs.forEach((tab) => {
        tab.isActive = this.$route.name === tab.to.name
      })
    } else {
      this.selectTab(this.internalSelectedIndex)
    }
  },
  methods: {
    isActive(i) {
      if (this.navigation) {
        return this.$route.name === this.tabs[i].to.name
      } else {
        return this.internalSelectedIndex === i
      }
    },
    getHref(i) {
      if (this.navigation) {
        const tab = this.tabs[i]
        return !tab.disabled ? this.$router.match(tab.to).path : null
      } else {
        return null
      }
    },
    selectTab(i) {
      if (this.navigation) {
        this.$emit('update:selected-index', i)
        this.$router.push(this.tabs[i].to)
      } else {
        this.$emit('update:selected-index', i)
        this.internalSelectedIndex = i
      }
      this.tabs.forEach((tab, index) => {
        tab.isActive = index === i
      })
    },
  },
}
</script>
