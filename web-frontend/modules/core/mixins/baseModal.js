import MoveToBody from '@baserow/modules/core/mixins/moveToBody'

export default {
  mixins: [MoveToBody],
  data() {
    return {
      open: false,
    }
  },
  destroyed() {
    window.removeEventListener('keyup', this.keyup)
  },
  methods: {
    /**
     * Toggle the open state of the modal.
     */
    toggle(value) {
      if (value === undefined) {
        value = !this.open
      }

      if (value) {
        this.show()
      } else {
        this.hide()
      }
    },
    /**
     * Show the modal.
     */
    show() {
      this.open = true
      this.$emit('show')
      window.addEventListener('keyup', this.keyup)
      document.body.classList.add('prevent-scroll')
    },
    /**
     * Hide the modal.
     */
    hide(emit = true) {
      // This is a temporary fix. What happens is the model is opened by a context menu
      // item and the user closes the modal, the element is first deleted and then the
      // click outside event of the context is fired. It then checks if the click was
      // inside one of his children, but because the modal element doesn't exists
      // anymore it thinks it was outside, so is closes the context menu which we don't
      // want automatically.
      setTimeout(() => {
        this.open = false
      })

      if (emit) {
        this.$emit('hidden')
      }

      window.removeEventListener('keyup', this.keyup)
      document.body.classList.remove('prevent-scroll')
    },
    /**
     * If someone actually clicked on the modal wrapper and not one of his children the
     * modal should be closed.
     */
    outside(event) {
      if (event.target === this.$refs.modalWrapper) {
        this.hide()
      }
    },
    /**
     * When the escape key is pressed the modal needs to be hidden.
     */
    keyup(event) {
      if (event.keyCode === 27) {
        this.hide()
      }
    },
  },
}
