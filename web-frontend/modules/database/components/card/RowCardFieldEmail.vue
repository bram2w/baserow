<template functional>
  <div class="card-text">
    <a :href="'mailto:' + props.value" target="_blank">{{ props.value }}</a>
  </div>
</template>

<script>
export default {
  height: 16,
}
</script>
