export default {
  props: {
    table: {
      type: Object,
      required: true,
    },
    fieldType: {
      type: String,
      required: false,
      default: '',
    },
  },
}
