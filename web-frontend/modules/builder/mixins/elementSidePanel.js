import { mapActions, mapGetters } from 'vuex'
import _ from 'lodash'

import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  inject: ['builder'],
  computed: {
    ...mapGetters({
      element: 'element/getSelected',
      page: 'page/getSelected',
    }),

    elementType() {
      if (this.element) {
        return this.$registry.get('element', this.element.type)
      }
      return null
    },

    parentElement() {
      return this.$store.getters['element/getElementById'](
        this.element?.parent_element_id
      )
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

      if (!this.$refs.panelForm.isFormValid()) {
        return
      }

      if (!_.isEqual(newValues, oldValues)) {
        try {
          await this.actionDebouncedUpdateSelectedElement({
            // Here we clone the values to prevent
            // "modification outside of the store" error
            values: clone(newValues),
          })
        } catch (error) {
          // Restore the previous saved values from the store
          this.$refs.panelForm.reset()
          notifyIf(error)
        }
      }
    },
  },
}
