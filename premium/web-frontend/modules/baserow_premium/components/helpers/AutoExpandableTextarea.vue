<template>
  <div
    class="auto-expandable-textarea__container"
    :class="{
      'auto-expandable-textarea--loading-overlay': loading,
    }"
  >
    <div v-if="loading" class="auto-expandable-textarea--loading"></div>
    <textarea
      ref="inputTextArea"
      v-model="innerValue"
      :placeholder="placeholder"
      class="input auto-expandable-textarea"
      :style="{
        height: textBoxSize + 'px',
        overflow: textBoxOverflow,
      }"
      rows="1"
      @keydown.enter.exact.prevent="$emit('entered')"
    />
  </div>
</template>
<script>
export default {
  name: 'AutoExpandableTextarea',
  props: {
    value: {
      required: true,
      type: String,
    },
    loading: {
      required: false,
      default: false,
      type: Boolean,
    },
    placeholder: {
      required: false,
      type: String,
      default: '',
    },
    maxRows: {
      required: false,
      type: Number,
      default: 4,
    },
    startingRows: {
      required: false,
      type: Number,
      default: 1,
    },
  },
  data() {
    return {
      numTextAreaLines: this.startingRows,
    }
  },
  computed: {
    innerValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('input', value)
      },
    },
    textBoxSize() {
      return 22 * Math.min(this.numTextAreaLines, 4)
    },
    textBoxOverflow() {
      return this.numTextAreaLines > 4 ? 'auto' : 'hidden'
    },
  },
  watch: {
    value() {
      this.resizeTextArea()
    },
  },
  methods: {
    resizeTextArea() {
      this.$nextTick(() => {
        const inputTextArea = this.$refs.inputTextArea
        this.numTextAreaLines = this.calculateHeight(inputTextArea)
      })
    },
    /**
     * Taken from https://stackoverflow.com/questions/1760629/how-to-get-number-of-rows-in-textarea-using-javascript/1761203#1761203
     *
     * The key reason we need this is to resize a fully expanded textarea to something
     * smaller as a user deletes newlines or text. Hence we need to actually manipulate
     * the dom and lower the height of the textarea until we find overflow is occurring
     * again to re-find the correct min height.
     */
    calculateContentHeight(ta, scanAmount) {
      const origHeight = ta.style.height
      let height = ta.offsetHeight
      const scrollHeight = ta.scrollHeight
      const overflow = ta.style.overflow
      /// only bother if the ta is bigger than content
      if (height >= scrollHeight) {
        /// check that our browser supports changing dimension
        /// calculations mid-way through a function call...
        ta.style.height = height + scanAmount + 'px'
        /// because the scrollbar can cause calculation problems
        ta.style.overflow = 'hidden'
        /// by checking that scrollHeight has updated
        if (scrollHeight < ta.scrollHeight) {
          /// now try and scan the ta's height downwards
          /// until scrollHeight becomes larger than height
          while (ta.offsetHeight >= ta.scrollHeight) {
            ta.style.height = (height -= scanAmount) + 'px'
          }
          /// be more specific to get the exact height
          while (ta.offsetHeight < ta.scrollHeight) {
            ta.style.height = height++ + 'px'
          }
          height--
          /// reset the ta back to it's original height
          ta.style.height = origHeight
          /// put the overflow back
          ta.style.overflow = overflow
          return height
        }
      } else {
        return scrollHeight
      }
    },
    calculateHeight(ta) {
      const style = window.getComputedStyle
        ? window.getComputedStyle(ta)
        : ta.currentStyle

      // This will get the line-height only if it is set in the css,
      // otherwise it's "normal"
      const taLineHeight = parseInt(style.lineHeight, 10)
      // Get the scroll height of the textarea
      const taHeight = this.calculateContentHeight(ta, taLineHeight)
      // calculate the number of lines
      return Math.ceil(taHeight / taLineHeight)
    },
  },
}
</script>
