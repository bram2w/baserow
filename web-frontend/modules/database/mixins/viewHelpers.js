import { notifyIf } from '@baserow/modules/core/utils/error'

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
    /**
     * Toggle the visibility for the field provided
     */
    async toggleFieldVisibility({ field }) {
      const exists = Object.prototype.hasOwnProperty.call(
        this.fieldOptions,
        field.id
      )
      const currentlyHidden = exists && this.fieldOptions[field.id].hidden
      try {
        await this.$store.dispatch(
          `${this.storePrefix}view/${this.view.type}/updateFieldOptionsOfField`,
          {
            field,
            values: { hidden: !currentlyHidden },
            oldValues: { hidden: currentlyHidden },
            readOnly: this.readOnly,
          }
        )
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    /**
     * Called when the user change the visibleFields order from the RowEditModal.
     */
    async orderFields({ newOrder }) {
      try {
        await this.$store.dispatch(
          `${this.storePrefix}view/${this.view.type}/updateFieldOptionsOrder`,
          {
            order: newOrder,
          }
        )
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
