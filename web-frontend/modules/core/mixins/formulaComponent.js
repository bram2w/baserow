import { nodeViewProps } from '@tiptap/vue-2'

export default {
  props: nodeViewProps,
  methods: {
    emitToEditor(...args) {
      this.$parent.$emit(...args)
    },
  },
}
