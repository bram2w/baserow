import { mapActions } from 'vuex'
import element from '@baserow/modules/builder/mixins/element'
import { FormContainerElementType } from '@baserow/modules/builder/elementTypes'

export default {
  mixins: [element],
  data() {
    return {
      inputValue: null,
    }
  },
  computed: {
    formElementData() {
      return this.$store.getters['formData/getFormData'](this.page)[
        this.element.id
      ]
    },
    elementFormDataValue() {
      return this.formElementData?.value
    },
    displayFormDataError() {
      return (
        this.formElementTouched &&
        !this.formElementData?.isValid &&
        !this.isEditMode
      )
    },
    formElementTouched() {
      return this.$store.getters['formData/getElementTouched'](
        this.page,
        this.element.id
      )
    },
    /**
     * Returns whether the form element is a descendant of a form container.
     * @returns {Boolean} If one or more ancestors is a form container.
     */
    isDescendantOfFormContainer() {
      return this.$store.getters['element/getAncestors'](
        this.page,
        this.element
      ).some(({ type }) => type === FormContainerElementType.getType())
    },
  },
  methods: {
    ...mapActions({
      actionSetFormData: 'formData/setFormData',
    }),
    /*
     * When a form element has been modified (e.g. a user has inputted a value),
     * this method is responsible for updating the form data in the store, and
     * if it's not inside a form container, marking the form element as having
     * been 'touched' by the user.
     */
    handleFormElementChange(value) {
      this.setFormData(value)
      if (!this.isDescendantOfFormContainer) {
        this.onFormElementTouch()
      }
    },
    setFormData(value) {
      return this.actionSetFormData({
        page: this.page,
        elementId: this.element.id,
        payload: {
          value,
          touched: this.formElementTouched,
          type: this.elementType.formDataType,
          isValid: this.elementType.isValid(this.element, value),
        },
      })
    },
    /**
     * Responsible for marking this form element as being 'touched' by a
     * user. This will help influence whether to display validation errors.
     */
    onFormElementTouch() {
      this.$store.dispatch('formData/setElementTouched', {
        page: this.page,
        wasTouched: true,
        elementId: this.element.id,
      })
    },
  },
  watch: {
    /**
     * When a form element's formData value changes.
     */
    elementFormDataValue: {
      handler(newValue) {
        this.inputValue = newValue
      },
      immediate: true,
    },
    inputValue(newValue) {
      this.handleFormElementChange(newValue)
    },
  },
}
