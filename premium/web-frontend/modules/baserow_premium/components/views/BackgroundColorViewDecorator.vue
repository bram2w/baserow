<template functional>
  <div
    :class="
      props.value ? `${data.class || ''} background-color--${props.value}` : ''
    "
  >
    <slot />
  </div>
</template>

<script>
export default {
  name: 'BackgroundColorViewDecorator',
  props: {
    value: {
      type: String,
      required: true,
    },
  },
}
</script>
