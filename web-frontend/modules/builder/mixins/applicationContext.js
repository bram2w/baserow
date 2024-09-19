export default {
  inject: { injectedApplicationContext: { from: 'applicationContext' } },
  provide() {
    return {
      applicationContext: this.applicationContext,
    }
  },
  props: {
    applicationContextAdditions: {
      type: Object,
      required: false,
      default: undefined,
    },
  },
  computed: {
    applicationContext() {
      return {
        ...this.injectedApplicationContext,
        ...this.applicationContextAdditions,
      }
    },
  },
}
