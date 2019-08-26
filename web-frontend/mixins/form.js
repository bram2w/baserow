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
  mounted() {
    Object.assign(this.values, this.values, this.defaultValues)
  },
  methods: {
    submit() {
      this.$v.$touch()
      if (!this.$v.$invalid) {
        this.$emit('submitted', this.values)
      }
    },
    reset() {
      Object.assign(
        this.values,
        this.$options.data.call(this).values,
        this.defaultValues
      )
      this.$v.$reset()
    }
  }
}
