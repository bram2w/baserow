import element from '@baserow/modules/builder/mixins/element'

export default {
  mixins: [element],
  props: {
    children: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
}
