import { mapActions } from 'vuex'
import element from '@baserow/modules/builder/mixins/element'

export default {
  mixins: [element],
  methods: {
    ...mapActions({
      actionSetFormData: 'formData/setFormData',
      actionRemoveFormData: 'formData/removeFormData',
    }),
    setFormData(value) {
      return this.actionSetFormData({
        page: this.page,
        elementId: this.element.id,
        payload: {
          value,
          type: this.elementType.formDataType,
        },
      })
    },
  },
}
