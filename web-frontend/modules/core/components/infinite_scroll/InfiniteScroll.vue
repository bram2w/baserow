<template>
  <section class="infinite-scroll" @scroll="handleScroll">
    <slot />
  </section>
</template>

<script>
export default {
  props: {
    currentCount: {
      type: Number,
      required: true,
    },
    maxCount: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      currentPage: 1,
    }
  },
  methods: {
    handleScroll({ target: { scrollTop, clientHeight, scrollHeight } }) {
      if (scrollTop + clientHeight >= scrollHeight) this.loadNextPage()
    },
    loadNextPage() {
      if (this.currentCount < this.maxCount) {
        this.currentPage = this.currentPage + 1
        this.$emit('load-next-page', this.currentPage)
      }
    },
  },
}
</script>
