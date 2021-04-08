<template>
  <div
    v-if="open"
    ref="modalWrapper"
    class="modal__wrapper"
    @click="outside($event)"
  >
    <div
      class="modal__box"
      :class="{
        'modal__box--with-sidebar': sidebar,
        'modal__box--full-screen': fullScreen,
      }"
    >
      <a v-if="closeButton" class="modal__close" @click="hide()">
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
import baseModal from '@baserow/modules/core/mixins/baseModal'

export default {
  name: 'Modal',
  mixins: [baseModal],
  props: {
    sidebar: {
      type: Boolean,
      default: false,
      required: false,
    },
    fullScreen: {
      type: Boolean,
      default: false,
      required: false,
    },
    closeButton: {
      type: Boolean,
      default: true,
      required: false,
    },
  },
}
</script>
