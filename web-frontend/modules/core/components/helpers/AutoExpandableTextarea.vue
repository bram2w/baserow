<template>
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
    @click="$emit('click', $event)"
    @keyup="$emit('keyup', $event)"
    @keydown="$emit('keydown', $event)"
    @blur="$emit('blur', $event)"
  />
</template>
<script>
/**
 * A blank textarea with no surrounding box styling (see AutoExpandableTextareaInput if
 * you want a nice styled box around this) which will automatically expand given the
 * users input to the maximum number of rows specified by the maxRows prop.
 */
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
      return 22 * Math.min(this.numTextAreaLines, this.maxRows)
    },
    textBoxOverflow() {
      return this.numTextAreaLines > this.maxRows ? 'auto' : 'hidden'
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
        } else {
          // We weren't able to resize this element inside this function call to figure
          // out it's true height so we give up and just return the scrollHeight.
          return scrollHeight
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
