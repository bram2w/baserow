<template>
  <a class="element-preview__insert" @click="$emit('click')">
    <i class="fas fa-plus"></i>
  </a>
</template>

<script>
export default {
  name: 'InsertElementButton',
}
</script>
