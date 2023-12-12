import element from '@baserow/modules/builder/mixins/element'
import { mapActions, mapGetters } from 'vuex'
import { PLACEMENTS } from '@baserow/modules/builder/enums'
import flushPromises from 'flush-promises'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  mixins: [element],
  props: {
    children: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  computed: {
    ...mapGetters({
      elementSelected: 'element/getSelected',
    }),
    PLACEMENTS: () => PLACEMENTS,
    elementSelectedId() {
      return this.elementSelected?.id
    },
  },
  methods: {
    ...mapActions({
      actionMoveElement: 'element/move',
    }),
    getPlacementsDisabledVertical(index) {
      const placementsDisabled = []

      if (index === 0) {
        placementsDisabled.push(PLACEMENTS.BEFORE)
      }

      if (index === this.children.length - 1) {
        placementsDisabled.push(PLACEMENTS.AFTER)
      }

      return placementsDisabled
    },
    async moveVertical(child, index, placement) {
      // Wait for the event propagation to be stopped by the child element otherwise
      // the click event select the container because the element is removed from the
      // DOM too quickly
      await flushPromises()

      // BeforeElementId remains null if we are moving the element at the end of the
      // list
      let beforeElementId = null

      if (placement === PLACEMENTS.BEFORE) {
        beforeElementId = this.children[index - 1].id
      } else if (index + 2 < this.children.length) {
        beforeElementId = this.children[index + 2].id
      }

      try {
        await this.actionMoveElement({
          page: this.page,
          elementId: child.id,
          beforeElementId,
          parentElementId: this.element.id,
          placeInContainer: child.placeInContainer,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
