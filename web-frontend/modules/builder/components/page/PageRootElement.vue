<template>
  <div :style="baseStyles">
    <div class="page-root-element__inner">
      <component
        :is="component"
        :element="element"
        :children="children"
        class="element"
      />
    </div>
  </div>
</template>

<script>
import PageElement from '@baserow/modules/builder/mixins/pageElement'

export default {
  name: 'PageRootElement',
  mixins: [PageElement],
}
</script>
