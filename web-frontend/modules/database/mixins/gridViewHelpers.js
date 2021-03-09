import { mapGetters } from 'vuex'

export default {
  data() {
    return {
      gridViewRowDetailsWidth: 60,
    }
  },
  computed: {
    ...mapGetters({
      fieldOptions: 'view/grid/getAllFieldOptions',
    }),
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
