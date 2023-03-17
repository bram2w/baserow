<template>
  <a class="select__footer-create-link" v-on="$listeners">
    <span>
      <i class="select__footer-create-icon fas fa-stream"></i>
      {{ $t('addElementButton.label') }}
    </span>
  </a>
</template>

<script>
export default {
  name: 'AddElementButton',
}
</script>
