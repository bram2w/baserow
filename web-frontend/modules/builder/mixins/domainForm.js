import form from '@baserow/modules/core/mixins/form'

export default {
  mixins: [form],
  props: {
    domain: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      serverErrors: {},
    }
  },
  computed: {
    hasServerErrors() {
      return Object.values(this.serverErrors).some((value) => value !== null)
    },
    hasError() {
      return !this.isFormValid() || this.hasServerErrors
    },
  },
  watch: {
    hasError: {
      handler(value) {
        this.$emit('error', value)
      },
      immediate: true,
    },
  },
  methods: {
    handleServerError(error) {
      if (error.handler.code !== 'ERROR_REQUEST_BODY_VALIDATION') return false

      this.serverErrors = Object.fromEntries(
        Object.entries(error.handler.detail || {}).map(([key, value]) => [
          key,
          value[0],
        ])
      )

      return true
    },
  },
}
