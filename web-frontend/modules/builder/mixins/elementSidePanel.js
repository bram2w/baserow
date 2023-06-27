import { mapActions, mapGetters } from 'vuex'
import _ from 'lodash'

import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  inject: ['builder'],
  computed: {
    ...mapGetters({
      element: 'element/getSelected',
    }),

    elementType() {
      if (this.element) {
        return this.$registry.get('element', this.element.type)
      }
      return null
    },

    defaultValues() {
      return this.element
    },
  },
  methods: {
    ...mapActions({
      actionDebouncedUpdateSelectedElement: 'element/debouncedUpdateSelected',
    }),
    async onChange(newValues) {
      const oldValues = this.element
      if (!_.isEqual(newValues, oldValues)) {
        try {
          await this.actionDebouncedUpdateSelectedElement({
            // Here we clone the values to prevent
            // "modification oustide of the store" error
            values: clone(newValues),
          })
        } catch (error) {
          // Restore the previous saved values from the store
          this.$refs.elementForm.reset()
          notifyIf(error)
        }
      }
    },
  },
}
