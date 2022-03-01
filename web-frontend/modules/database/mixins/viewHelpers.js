export default {
  methods: {
    /**
     * Must be called when a new field is created. It emits the refresh event when
     * needed. It expects the event parameter propagated from the
     * `CreateFieldContext` component.
     */
    fieldCreated({ fetchNeeded, ...context }) {
      const viewType = this.$registry.get('view', this.view.type)

      if (
        fetchNeeded ||
        viewType.shouldRefreshWhenFieldCreated(
          this.$registry,
          this.$store,
          context.newField,
          this.storePrefix
        )
      ) {
        this.$emit('refresh', context)
      } else if (context.callback) {
        context.callback()
      }
    },
  },
}
