<template>
  <input
    type="text"
    class="input-element"
    :readonly="isEditable"
    :value="element.default_value"
    :required="element.required"
    :placeholder="element.placeholder"
  />
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'

export default {
  name: 'InputTextElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {string} default_value - The text input's default value.
     * @property {boolean} required - Whether the text input is required.
     * @property {Object} placeholder - The text input's placeholder value.
     */
    element: {
      type: Object,
      required: true,
    },
  },
}
</script>
