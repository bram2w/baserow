/**
 * A mixin that can be used by a row edit modal component. It introduces the props that
 * will be passed by the RowEditModalField component.
 */
export default {
  props: {
    /**
     * Contains the field type object. Because each field type can have different
     * settings you need this in order to render the correct component or implement
     * correct validation.
     */
    field: {
      type: Object,
      required: true,
    },
    /**
     * The value of the grid field, this could for example for a number field 10,
     * text field 'Random string' etc.
     */
    value: {
      type: [String, Number, Object, Boolean, Array],
      required: false,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
}
