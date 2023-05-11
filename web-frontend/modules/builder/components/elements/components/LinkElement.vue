<template>
  <div class="link-element" :class="classes">
    <Button
      v-if="element.variant === 'button'"
      type="link"
      v-bind="extraAttr"
      :target="element.target"
      :full-width="element.width === 'full'"
      @click="onClick($event)"
    >
      {{ element.value || $t('linkElement.noValue') }}
    </Button>
    <a
      v-else
      class="link-element__link"
      v-bind="extraAttr"
      :target="`_${element.target}`"
      @click="onClick($event)"
    >
      {{ element.value || $t('linkElement.noValue') }}
    </a>
  </div>
</template>

<script>
import textElement from '@baserow/modules/builder/mixins/elements/textElement'
import { LinkElementType } from '@baserow/modules/builder/elementTypes'

/**
 * @typedef LinkElement
 * @property {string} value The text inside the button
 * @property {string} alignment left|center|right
 * @property {string} variant link|button
 * @property {string} navigation_type page|custom
 * @property {string} navigate_to_page_id The page id for `page` navigation type.
 * @property {object} page_parameters the page paramaters
 * @property {string} navigate_to_url The URL for `custom` navigation type.
 * @property {string} target self|blank
 */

export default {
  name: 'LinkElement',
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
    mode: { type: String, required: true },
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
      if (this.isExternalLink) {
        attr.rel = 'noopener noreferrer'
      }
      return attr
    },
    originalUrl() {
      try {
        return LinkElementType.getUrlFromElement(this.element, this.builder)
      } catch (e) {
        return ''
      }
    },
    url() {
      if (
        this.originalUrl &&
        this.mode === 'preview' &&
        (this.element.navigation_type === 'page' ||
          (this.element.navigation_type === 'custom' &&
            this.originalUrl.startsWith('/')))
      ) {
        // Add prefix in preview mode for page navigation or custom URL starting
        // with `/`
        return `/builder/${this.builder.id}/preview${this.originalUrl}`
      } else {
        return this.originalUrl
      }
    },
    isExternalLink() {
      return (
        this.element.navigation_type === 'custom' &&
        !this.originalUrl.startsWith('/')
      )
    },
  },
  methods: {
    onClick(event) {
      if (!this.url) {
        event.preventDefault()
      } else if (
        this.element.navigation_type === 'page' &&
        this.element.target !== 'blank'
      ) {
        event.preventDefault()
        this.$router.push(this.url)
      }
    },
  },
}
</script>
