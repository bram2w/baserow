<template>
  <div
    class="auto-expandable-textarea__container"
    :class="{
      'auto-expandable-textarea--loading-overlay': loading,
    }"
  >
    <div v-if="loading" class="auto-expandable-textarea--loading"></div>
    <AutoExpandableTextarea
      v-model="innerValue"
      :placeholder="placeholder"
      :max-rows="maxRows"
      :starting-rows="startingRows"
      @keydown.enter.exact.prevent="$emit('entered')"
    >
    </AutoExpandableTextarea>
  </div>
</template>
<script>
import AutoExpandableTextarea from '@baserow/modules/core/components/helpers/AutoExpandableTextarea'

/**
 * A textarea styled as an input box which will automatically expand given the users
 * input to the maximum number of rows specified by the maxRows prop. Prevents enter
 * by default and instead emits an 'entered' event for the parent to handle. Also shows
 * a loading overlay when the loading prop is set to true.
 */
export default {
  name: 'AutoExpandableTextareaInput',
  components: {
    AutoExpandableTextarea,
  },
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
  computed: {
    innerValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('input', value)
      },
    },
  },
}
</script>
