<template>
  <span>{{ value }}</span>
</template>

<script>
export default {
  name: 'TextField',
  props: {
    value: {
      type: String,
      required: true,
    },
  },
}
</script>
