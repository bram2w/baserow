<template>
  <div class="filters__value-timezone">{{ value }}</div>
</template>

<script>
export default {
  name: 'ViewFilterTypeText',
  props: {
    value: {
      type: String,
      required: true,
    },
  },
}
</script>
