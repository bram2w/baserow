<template>
  <div
    class="link-element"
    :class="classes"
    :style="{
      '--button-color': resolveColor(element.button_color, colorVariables),
    }"
  >
    <ABLink
      v-bind="extraAttr"
      :full-width="element.width === WIDTHS.FULL.value"
      :target="`_${element.target}`"
      :variant="element.variant"
      @click.prevent="onClick"
    >
      {{ resolvedValue || $t('linkElement.noValue') }}
    </ABLink>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { WIDTHS } from '@baserow/modules/builder/enums'
import resolveElementUrl from '@baserow/modules/builder/utils/urlResolution'
import { ensureString } from '@baserow/modules/core/utils/validator'

/**
 * @typedef LinkElement
 * @property {string} value The text inside the button
 * @property {string} alignment left|center|right
 * @property {string} width auto|full
 * @property {string} variant link|button
 * @property {string} navigation_type page|custom
 * @property {string} navigate_to_page_id The page id for `page` navigation type.
 * @property {object} page_parameters the page parameters
 * @property {string} navigate_to_url The URL for `custom` navigation type.
 * @property {string} target self|blank
 */

export default {
  name: 'LinkElement',
  mixins: [element],
  props: {
    /**
     * @type {LinkElement}
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    WIDTHS: () => WIDTHS,
    resolvedValue() {
      return ensureString(this.resolveFormula(this.element.value))
    },
    classes() {
      return {
        [`element--alignment-horizontal-${this.element.alignment}`]: true,
        'element--no-value': !this.resolvedValue,
      }
    },
    extraAttr() {
      const attr = {}
      if (this.urlContext.url) {
        attr.href = this.urlContext.url
      }
      if (this.urlContext.isExternalLink) {
        attr.rel = 'noopener noreferrer'
      }
      return attr
    },
    urlContext() {
      try {
        return resolveElementUrl(
          this.element,
          this.builder,
          this.resolveFormula,
          this.mode
        )
      } catch (e) {
        return {
          url: '',
          isExternalLink: false,
        }
      }
    },
  },
  methods: {
    onClick(event) {
      const url = this.urlContext.url
      if (this.mode === 'editing' || !url) {
        return
      }
      if (this.element.target !== 'blank') {
        if (this.element.navigation_type === 'custom') {
          window.location.href = url
        } else if (this.element.navigation_type === 'page') {
          this.$router.push(url)
        }
      } else {
        window.open(url, '_blank')
      }
    },
  },
}
</script>
