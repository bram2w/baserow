<template functional>
  <div class="card-text">
    {{ props.value !== 'NaN' ? props.value : 'Invalid Number' }}
  </div>
</template>

<script>
export default {
  height: 16,
}
</script>
