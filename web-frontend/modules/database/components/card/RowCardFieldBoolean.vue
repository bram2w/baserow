<template functional>
  <div class="card-boolean">
    <i v-if="!!props.value" class="fas fa-check"></i>
  </div>
</template>

<script>
export default {
  height: 13,
}
</script>
