export default {
  props: {
    element: {
      type: Object,
      required: true,
    },
    builder: {
      type: Object,
      required: true,
    },
    mode: {
      // editing = being editing by the page editor
      // preview = previewing the application
      // public = publicly published application
      type: String,
      required: false,
      default: '',
    },
  },
}
