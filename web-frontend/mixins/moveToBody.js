export default {
  /**
   * Because we don't want the parent context to close when a user clicks 'outside' that
   * element and in the child element we need to register the child with their parent to
   * prevent this.
   */
  mounted() {
    let $parent = this.$parent
    while ($parent !== undefined) {
      if ($parent.registerContextChild) {
        $parent.registerContextChild(this)
      }
      $parent = $parent.$parent
    }

    // Move the rendered element to the top of the body so it can be positioned over any
    // other element.
    const body = document.body
    body.insertBefore(this.$el, body.firstChild)
  },
  /**
   * Make sure the context menu is not open and all the events on the body are removed
   * and that the element is removed from the body.
   */
  destroyed() {
    this.hide()

    if (this.$el.parentNode) {
      this.$el.parentNode.removeChild(this.$el)
    }
  }
}
