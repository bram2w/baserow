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
      }
    }
  },
  data() {
    return {
      // A list of values that the form allows. If null all values are allowed.
      allowedValues: null
    }
  },
  mounted() {
    Object.assign(this.values, this.values, this.getDefaultValues())
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
        if (this.allowedValues.indexOf(key) > -1) {
          result[key] = this.defaultValues[key]
        }
        return result
      }, {})
    },
    submit() {
      this.$v.$touch()
      if (this.isFormValid()) {
        this.$emit('submitted', this.getFormValues())
      }
    },
    /**
     * Returns true is everything is valid.
     */
    isFormValid() {
      return !this.$v.$invalid && this.areChildFormsValid()
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
        ...this.$children.map(child => {
          return 'getChildFormsValues' in child ? child.getFormValues() : {}
        })
      )
    },
    /**
     * Resets the form to its original state.
     */
    reset() {
      Object.assign(
        this.values,
        this.$options.data.call(this).values,
        this.getDefaultValues()
      )
      this.$v.$reset()
    }
  }
}
