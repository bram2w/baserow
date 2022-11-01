<template>
  <img v-if="icon" :src="icon" class="auth-provider-icon" />
</template>

<script>
export default {
  props: {
    icon: {
      type: String,
      required: true,
    },
  },
}
</script>
