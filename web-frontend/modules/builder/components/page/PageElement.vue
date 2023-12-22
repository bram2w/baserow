<template>
  <div
    class="element__wrapper"
    :class="{
      'element__wrapper--full-width':
        element.style_width === WIDTH_TYPES.FULL.value,
      'element__wrapper--medium-width':
        element.style_width === WIDTH_TYPES.MEDIUM.value,
      'element__wrapper--small-width':
        element.style_width === WIDTH_TYPES.SMALL.value,
    }"
    :style="wrapperStyles"
  >
    <div class="element__inner-wrapper" :style="innerWrapperStyles">
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
import pageElement from '@baserow/modules/builder/mixins/pageElement'

export default {
  name: 'PageElement',
  mixins: [pageElement],
}
</script>
