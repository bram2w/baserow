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
        'modal__box--full-height': fullHeight,
        'modal__box--with-sidebar': sidebar,
        'modal__box--full-screen': fullScreen,
        'modal__box--small': small,
        'modal__box--tiny': tiny,
      }"
    >
      <template v-if="sidebar">
        <div
          v-if="leftSidebar"
          class="modal__box-sidebar modal__box-sidebar--left"
          :class="{ 'modal__box-sidebar--scrollable': leftSidebarScrollable }"
        >
          <slot name="sidebar"></slot>
        </div>
        <div
          class="modal__box-content"
          :class="{ 'modal__box-content--scrollable': contentScrollable }"
        >
          <slot name="content"></slot>
          <a
            v-if="closeButton && canClose"
            class="modal__close"
            @click="hide()"
          >
            <i class="fas fa-times"></i>
          </a>
        </div>
        <div
          v-if="rightSidebar"
          class="modal__box-sidebar modal__box-sidebar--right"
          :class="{ 'modal__box-sidebar--scrollable': rightSidebarScrollable }"
        >
          <slot name="sidebar"></slot>
        </div>
      </template>
      <template v-if="!sidebar">
        <slot></slot>
        <slot name="content"></slot>
        <a v-if="closeButton && canClose" class="modal__close" @click="hide()">
          <i class="fas fa-times"></i>
        </a>
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
    leftSidebar: {
      type: Boolean,
      default: false,
      required: false,
    },
    rightSidebar: {
      type: Boolean,
      default: false,
      required: false,
    },
    fullScreen: {
      type: Boolean,
      default: false,
      required: false,
    },
    small: {
      type: Boolean,
      default: false,
      required: false,
    },
    tiny: {
      type: Boolean,
      default: false,
      required: false,
    },
    closeButton: {
      type: Boolean,
      default: true,
      required: false,
    },
    fullHeight: {
      type: Boolean,
      default: false,
      required: false,
    },
    leftSidebarScrollable: {
      type: Boolean,
      default: false,
      required: false,
    },
    contentScrollable: {
      type: Boolean,
      default: false,
      required: false,
    },
    rightSidebarScrollable: {
      type: Boolean,
      default: false,
      required: false,
    },
    canClose: {
      type: Boolean,
      default: true,
      required: false,
    },
  },
  computed: {
    sidebar() {
      return this.leftSidebar || this.rightSidebar
    },
  },
}
</script>
