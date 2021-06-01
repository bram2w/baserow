<template>
  <span
    ref="editable"
    :contenteditable="editing"
    :class="{ 'forced-user-select-initial': editing }"
    @input="update"
    @keydown="keydown"
    @focusout="change"
    @paste="paste"
    >{{ value }}</span
  >
</template>

<script>
import { focusEnd } from '@baserow/modules/core/utils/dom'

export default {
  name: 'Editable',
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      editing: false,
      oldValue: '',
      newValue: '',
    }
  },
  watch: {
    value(value) {
      this.set(value)
    },
  },
  mounted() {
    this.set(this.value)
  },
  methods: {
    /**
     * This method must be called when the is going to be edited. It will enable the
     * contenteditable state and will focus the element.
     */
    edit() {
      this.editing = true
      this.$emit('editing', true)
      this.$nextTick(() => {
        focusEnd(this.$refs.editable)
      })
    },
    /**
     * This method is called when the value has changed and needs to be saved. It will
     * change the editing state and will emit a change event if the new value has
     * changed.
     */
    change() {
      this.editing = false
      this.$emit('editing', false)

      if (this.oldValue === this.newValue) {
        return
      }

      this.$emit('change', {
        oldValue: this.value,
        value: this.newValue,
      })
      this.oldValue = this.newValue
    },
    /**
     * Everytime a key is pressed inside the editable this event will be trigger which
     * will update the new value.
     */
    update(event) {
      const target = event.target
      const text = target.textContent
      this.newValue = text
    },
    /**
     * When someone pastes something we want to only insert the plain text instead of
     * the styled content.
     */
    paste(event) {
      event.preventDefault()
      const text = (event.originalEvent || event).clipboardData.getData(
        'text/plain'
      )
      document.execCommand('insertHTML', false, text)
    },
    /**
     * If a key is pressed and it is an enter or esc key the change event will be called
     * to end the editing and save the value.
     */
    keydown(event) {
      if (event.keyCode === 13 || event.keyCode === 27) {
        event.preventDefault()
        this.change()
        return false
      }
    },
    /**
     *
     */
    set(value) {
      this.oldValue = this.value
      this.newValue = this.value
      this.$refs.editable.textContent = this.value
    },
  },
}
</script>
