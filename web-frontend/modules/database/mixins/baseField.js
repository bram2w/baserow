/**
 * A mixin that can be used by a row edit modal component. It introduces the props that
 * will be passed by the RowEditModalField component.
 */
export default {
  props: {
    /**
     * The group ID of the group where parent table and database are in.
     */
    groupId: {
      type: Number,
      required: true,
    },
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
  },
  computed: {
    valid() {
      return this.isValid()
    },
    error() {
      return this.getError()
    },
  },
  methods: {
    isValid() {
      return this.getError() === null
    },
    getError() {
      return this.getValidationError(this.value)
    },
    /**
     * Should return a validation error message in string format if there is
     * any.
     */
    getValidationError(value) {
      const fieldType = this.$registry.get('field', this.field.type)
      const error = fieldType.getValidationError(this.field, value)
      return error
    },
  },
}
