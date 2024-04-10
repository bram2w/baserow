import element from '@baserow/modules/builder/mixins/element'
import { mapGetters } from 'vuex'
import { PLACEMENTS } from '@baserow/modules/builder/enums'

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
}
