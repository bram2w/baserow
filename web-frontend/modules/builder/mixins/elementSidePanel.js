import { mapActions, mapGetters } from 'vuex'
import _ from 'lodash'

import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'
import BigNumber from 'bignumber.js'

export default {
  inject: ['builder', 'page'],
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

    parentElement() {
      return this.$store.getters['element/getElementById'](
        this.page,
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
      if (newValues.order) {
        newValues.order = new BigNumber(newValues.order)
      }

      if (!this.$refs.panelForm.isFormValid()) {
        return
      }

      const differences = Object.fromEntries(
        Object.entries(newValues).filter(
          ([key, value]) => !_.isEqual(value, this.element[key])
        )
      )

      if (Object.keys(differences).length > 0) {
        try {
          await this.actionDebouncedUpdateSelectedElement({
            page: this.page,
            // Here we clone the values to prevent
            // "modification outside of the store" error
            values: clone(differences),
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
