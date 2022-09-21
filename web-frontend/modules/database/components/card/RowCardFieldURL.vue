<template functional>
  <div class="card-text">
    <a
      :href="props.value"
      target="_blank"
      rel="nofollow noopener noreferrer"
      class="forced-pointer-events-auto"
      @mousedown.stop
      >{{ props.value }}</a
    >
  </div>
</template>

<script>
export default {
  height: 16,
}
</script>
