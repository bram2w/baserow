/**
 * This mixin is for components that have the Context component as root element.
 * It will make it easier to call the root context specific functions.
 */
export default {
  methods: {
    getRootContext() {
      if (
        this.$children.length > 0 &&
        this.$children[0].$options.name === 'Context'
      ) {
        return this.$children[0]
      }
    },
    toggle(...args) {
      this.getRootContext().toggle(...args)
    },
    toggleNextToMouse(...args) {
      this.getRootContext().toggleNextToMouse(...args)
    },
    show(...args) {
      this.getRootContext().show(...args)
    },
    showNextToMouse(...args) {
      this.getRootContext().showNextToMouse(...args)
    },
    hide(...args) {
      this.getRootContext().hide(...args)
    },
  },
}
