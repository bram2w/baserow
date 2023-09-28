<template>
  <div
    class="avatar"
    :class="{
      'avatar--rounded': rounded,
      'avatar--icon': Boolean(icon),
      'avatar--image': Boolean(image),
      'avatar--initials': Boolean(initials),
      [`avatar--size-${size}`]: true,
      [`avatar--${color}`]: color,
    }"
  >
    <i v-if="icon" :class="`${icon}`" />
    <img v-if="image" :src="image" class="avatar__image" />
    <span v-if="initials">{{ initials }}</span>
  </div>
</template>

<script>
export default {
  name: 'Avatar',
  props: {
    image: {
      type: String,
      required: false,
      default: '',
    },
    icon: {
      type: String,
      required: false,
      default: '',
    },
    initials: {
      type: String,
      required: false,
      default: '',
    },
    rounded: {
      type: Boolean,
      required: false,
      default: true,
    },
    color: {
      //  primary - success - warning - error - ghost
      required: false,
      type: String,
      default: 'primary',
    },
    size: {
      // normal - large - tiny
      type: String,
      required: false,
      default: 'normal',
    },
  },
}
</script>
