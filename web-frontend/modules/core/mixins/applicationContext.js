export default {
  methods: {
    toggle(
      target,
      vertical = 'bottom',
      horizontal = 'left',
      verticalOffset = 10,
      horizontalOffset = 0,
      value
    ) {
      this.$refs.context.toggle(
        target,
        vertical,
        horizontal,
        verticalOffset,
        horizontalOffset,
        value
      )
    },
    hide() {
      this.$refs.context.hide()
    },
  },
}
