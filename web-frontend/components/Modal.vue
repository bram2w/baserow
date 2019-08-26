<template>
  <transition name="fade">
    <div
      v-if="open"
      ref="modalWrapper"
      class="modal-wrapper"
      @click="outside($event)"
    >
      <div class="modal-box">
        <a class="modal-close" @click="hide()">
          <i class="fas fa-times"></i>
        </a>
        <slot></slot>
      </div>
    </div>
  </transition>
</template>

<script>
import MoveToBody from '@/mixins/moveToBody'

export default {
  name: 'Modal',
  mixins: [MoveToBody],
  data() {
    return {
      open: false
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
      this.open = false
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
    }
  }
}
</script>
