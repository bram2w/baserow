<template functional>
  <a
    class="grid-view__row-more"
    @click="listeners['edit-modal'] && listeners['edit-modal']()"
  >
    <i class="iconoir-expand"></i>
  </a>
</template>
<script>
export default {
  name: 'GridViewRowExpandButton',
  functional: true,
}
</script>
