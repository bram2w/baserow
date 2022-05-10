<template functional>
  <div
    class="left-border-decorator"
    :class="props.value ? `background-color--${props.value}` : ''"
  ></div>
</template>

<script>
export default {
  name: 'LeftBorderColorViewDecorator',
  props: {
    value: {
      type: String,
      required: true,
    },
  },
}
</script>
