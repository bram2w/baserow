<template>
  <div
    v-if="open"
    ref="modalWrapper"
    class="modal__wrapper"
    @click="outside($event)"
  >
    <div class="modal__box" :class="{ 'modal__box--with-sidebar': sidebar }">
      <a class="modal__close" @click="hide()">
        <i class="fas fa-times"></i>
      </a>
      <template v-if="sidebar">
        <div class="modal__box-sidebar">
          <slot name="sidebar"></slot>
        </div>
        <div class="modal__box-content">
          <slot name="content"></slot>
        </div>
      </template>
      <template v-if="!sidebar">
        <slot></slot>
      </template>
    </div>
  </div>
</template>

<script>
import MoveToBody from '@baserow/modules/core/mixins/moveToBody'

export default {
  name: 'Modal',
  mixins: [MoveToBody],
  props: {
    sidebar: {
      type: Boolean,
      default: false,
      required: false,
    },
  },
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
      window.addEventListener('keyup', this.keyup)
    },
    /**
     * Hide the modal.
     */
    hide() {
      // This is a temporary fix. What happens is the model is opened by a context menu
      // item and the user closes the modal, the element is first deleted and then the
      // click outside event of the context is fired. It then checks if the click was
      // inside one of his children, but because the modal element doesn't exists
      // anymore it thinks it was outside, so is closes the context menu which we don't
      // want automatically.
      setTimeout(() => {
        this.open = false
      })
      this.$emit('hidden')
      window.removeEventListener('keyup', this.keyup)
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
     *
     */
    keyup(event) {
      if (event.keyCode === 27) {
        this.hide()
      }
    },
  },
}
</script>
