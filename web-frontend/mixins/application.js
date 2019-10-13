import { notify404 } from '@/utils/error'

/**
 * This mixin can be used in combination with the component where the
 * application routes to when selected. It will make sure that the application
 * preSelect action is called so that the all the depending information is
 * loaded. If something goes wrong while loading this information it will show a
 * standard error.
 */
export default {
  props: {
    id: {
      type: Number,
      required: true
    }
  },
  mounted() {
    this.$store.dispatch('application/preSelect', this.id).catch(error => {
      notify404(
        this.$store.dispatch,
        error,
        'Application not found.',
        "The application with the provided id doesn't exist or you " +
          "don't have access to it."
      )

      this.$nuxt.$router.push({ name: 'app' })
    })
  }
}
