<template>
  <div
    class="copied"
    :class="{
      'copied--show': visible,
      'copied--hide': hide,
    }"
  >
    {{ $t('copied.label') }}
  </div>
</template>

<script>
export default {
  name: 'Copied',
  data() {
    return {
      visible: false,
      hide: false,
    }
  },
  methods: {
    show() {
      this.visible = true
      setTimeout(() => {
        this.hide = true
        setTimeout(() => {
          this.visible = false
          this.hide = false
        }, 1000)
      }, 500)
    },
  },
}
</script>
