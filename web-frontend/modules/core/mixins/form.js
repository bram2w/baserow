import { clone } from '@baserow/modules/core/utils/object'

/**
 * This mixin introduces some helper functions for form components where the
 * whole component existence is based on being a form.
 */
export default {
  props: {
    defaultValues: {
      type: Object,
      required: false,
      default: () => {
        return {}
      },
    },
  },
  data() {
    return {
      // A list of values that the form allows. If null all values are allowed.
      allowedValues: null,
    }
  },
  mounted() {
    Object.assign(this.values, this.values, this.getDefaultValues())
  },
  watch: {
    values: {
      deep: true,
      handler(newValues) {
        this.$emit('values-changed', newValues)
      },
    },
  },
  methods: {
    /**
     * Returns all the provided default values, but if the allowedValues are set
     * an object only containing those values is returned. This could be useful
     * when the defaultValues also contain other values which must not be used
     * when submitting.
     */
    getDefaultValues() {
      if (this.allowedValues === null) {
        return this.defaultValues
      }
      return Object.keys(this.defaultValues).reduce((result, key) => {
        if (this.allowedValues.includes(key)) {
          let value = this.defaultValues[key]

          // If the value is an array or object, it could be that it contains
          // references and we actually need a copy of the value here so that we don't
          // directly change existing variables when editing form values.
          if (
            Array.isArray(value) ||
            (typeof value === 'object' && value !== null)
          ) {
            value = clone(value)
          }

          result[key] = value
        }
        return result
      }, {})
    },
    submit() {
      this.$v.$touch()

      // Also touch all the child forms so that all the error messages are going to
      // be displayed.
      for (const child of this.$children) {
        if ('isFormValid' in child && '$v' in child) {
          child.$v.$touch()
        }
      }

      if (this.isFormValid()) {
        this.$emit('submitted', this.getFormValues())
      }
    },
    /**
     * Returns true is everything is valid.
     */
    isFormValid() {
      // Some forms might not do any validation themselves. If they don't, then they
      // are by definition valid if their children are valid.
      const thisFormInvalid = '$v' in this && this.$v.$invalid
      return !thisFormInvalid && this.areChildFormsValid()
    },
    /**
     * Returns true if all the child form components are valid.
     */
    areChildFormsValid() {
      for (const child of this.$children) {
        if ('isFormValid' in child && !child.isFormValid()) {
          return false
        }
      }
      return true
    },
    /**
     * A method that can be overridden to do some mutations on the values before
     * calling the submitted event.
     */
    getFormValues() {
      return Object.assign({}, this.values, this.getChildFormsValues())
    },
    /**
     * Returns an object containing the values of the child forms.
     */
    getChildFormsValues() {
      return Object.assign(
        {},
        ...this.$children.map((child) => {
          return 'getChildFormsValues' in child ? child.getFormValues() : {}
        })
      )
    },
    /**
     * Resets the form and the child forms to its original state.
     */
    reset() {
      Object.assign(
        this.values,
        this.$options.data.call(this).values,
        this.getDefaultValues()
      )

      if ('$v' in this) {
        this.$v.$reset()
      }

      // Also reset the child forms.
      for (const child of this.$children) {
        if ('isFormValid' in child) {
          child.reset()
        }
      }
    },
  },
}
