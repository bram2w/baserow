<template>
  <div :style="baseStyles">
    <component
      :is="component"
      :element="element"
      :children="children"
      class="element"
    />
  </div>
</template>

<script>
import PageElement from '@baserow/modules/builder/mixins/pageElement'

export default {
  name: 'PageElement',
  mixins: [PageElement],
}
</script>
