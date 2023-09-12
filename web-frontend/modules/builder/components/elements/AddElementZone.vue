<template>
  <div class="add-element-zone" @click="$emit('add-element')">
    <div class="add-element-zone__content">
      <i class="fas fa-plus add-element-zone__icon"></i>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AddElementZone',
}
</script>
