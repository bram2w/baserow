<template functional>
  <!--
  This element is supposed to be wrapping the root elements on a page. They allow
  setting a width, background, borders, and more, but this only makes sense if they're
  added to the root of the page. Child elements in for example a containing element must
  not be wrapped by this component.
  -->
  <div
    class="page-root-element"
    :style="{
      'padding-top': `${props.element.style_padding_top || 0}px`,
      'padding-bottom': `${props.element.style_padding_bottom || 0}px`,
    }"
  >
    <div class="page-root-element__inner">
      <component
        :is="$options.methods.getComponent(parent, props.element, props.mode)"
        :element="props.element"
        :builder="props.builder"
        :mode="props.mode"
        :page="props.page"
        class="element"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'PageRootElement',
  props: {
    element: {
      type: Object,
      required: true,
    },
    builder: {
      type: Object,
      required: true,
    },
    page: {
      type: Object,
      required: true,
    },
    mode: {
      type: String,
      required: false,
      default: '',
    },
  },
  methods: {
    getComponent(parent, element, mode) {
      const elementType = parent.$registry.get('element', element.type)
      const componentName = mode === 'editing' ? 'editComponent' : 'component'
      return elementType[componentName]
    },
  },
}
</script>
