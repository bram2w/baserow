<template>
  <div class="link-element" :class="classes">
    <Button
      v-if="element.variant === 'button'"
      type="link"
      v-bind="extraAttr"
      :target="element.target"
      :full-width="element.width === 'full'"
      @click.prevent
    >
      {{ element.value || $t('linkElement.noValue') }}
    </Button>
    <a
      v-else
      class="link-element__link"
      v-bind="extraAttr"
      :target="`_${element.target}`"
      @click.prevent
    >
      {{ element.value || $t('linkElement.noValue') }}
    </a>
  </div>
</template>

<script>
import textElement from '@baserow/modules/builder/mixins/elements/textElement'
import { LinkElementType } from '@baserow/modules/builder/elementTypes'

export default {
  name: 'LinkElementEdit',
  mixins: [textElement],
  props: {
    /**
     * @type {LinkElement}
     */
    element: {
      type: Object,
      required: true,
    },
    builder: { type: Object, required: true },
  },
  computed: {
    classes() {
      return {
        [`link-element--alignment-${this.element.alignment}`]: true,
        'element--no-value': !this.element.value,
      }
    },
    extraAttr() {
      const attr = {}
      if (this.url) {
        attr.href = this.url
      }
      return attr
    },
    url() {
      try {
        return LinkElementType.getUrlFromElement(this.element, this.builder)
      } catch (e) {
        return ''
      }
    },
  },
}
</script>
