import { mapGetters } from 'vuex'

export default {
  props: {
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      gridViewRowDetailsWidth: 60,
    }
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        fieldOptions:
          this.$options.propsData.storePrefix + 'view/grid/getAllFieldOptions',
      }),
    }
  },
  methods: {
    getFieldWidth(fieldId) {
      const hasFieldOptions = Object.prototype.hasOwnProperty.call(
        this.fieldOptions,
        fieldId
      )

      if (hasFieldOptions && this.fieldOptions[fieldId].hidden) {
        return 0
      }

      return hasFieldOptions ? this.fieldOptions[fieldId].width : 200
    },
  },
}
