<template>
  <div
    :style="{
      '--button-color': resolveColor(element.button_color, colorVariables),
    }"
  >
    <div v-if="mode === 'editing' && children.length === 0">
      <AddElementZone @add-element="showAddElementModal"></AddElementZone>
      <AddElementModal
        ref="addElementModal"
        :page="page"
        :element-types-allowed="elementType.childElementTypes"
      ></AddElementModal>
    </div>
    <div v-else>
      <template v-for="(child, index) in children">
        <ElementPreview
          v-if="mode === 'editing'"
          :key="child.id"
          class="element"
          :element="child"
          :active="child.id === elementSelectedId"
          :index="index"
          :placements="[PLACEMENTS.BEFORE, PLACEMENTS.AFTER]"
          :placements-disabled="getPlacementsDisabledVertical(index)"
          @move="moveVertical(child, index, $event)"
        />
        <PageElement v-else :key="child.id" :element="child" :mode="mode" />
      </template>
    </div>
    <div class="form-container-element__submit-button margin-top-2">
      <button class="ab-button" @click="validateAndSubmitEvent">
        {{ submitButtonLabelResolved || $t('buttonElement.noValue') }}
      </button>
    </div>
  </div>
</template>

<script>
import AddElementZone from '@baserow/modules/builder/components/elements/AddElementZone.vue'
import containerElement from '@baserow/modules/builder/mixins/containerElement'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal.vue'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview.vue'
import PageElement from '@baserow/modules/builder/components/page/PageElement.vue'

export default {
  name: 'FormContainerElement',
  components: { PageElement, ElementPreview, AddElementModal, AddElementZone },
  mixins: [containerElement],
  props: {
    /**
     * @type {Object}
     * @property button_color - The submit button's color.
     * @property submit_button_label - The label of the submit button
     * @property reset_initial_values_post_submission - Whether to reset the form
     *  elements to their initial value or not, following a successful submission.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    submitButtonLabelResolved() {
      try {
        return this.resolveFormula(this.element.submit_button_label)
      } catch (e) {
        return ''
      }
    },
    getFormElementDescendants() {
      const descendants = this.$store.getters['element/getDescendants'](
        this.page,
        this.element
      )
      return descendants.filter((element) => {
        const elementType = this.$registry.get('element', element.type)
        return elementType.isFormElement
      })
    },
    /*
     * Responsible for determining if any of the form's form elements are invalid. They
     * will be if: 1) they don't have any form data, or 2) they have form data but their
     * value is invalid.
     */
    formElementChildrenAreInvalid() {
      return this.getFormElementDescendants.some(
        ({ id }) =>
          !Object.prototype.hasOwnProperty.call(this.page.formData, id) ||
          !this.page.formData[id].isValid
      )
    },
  },
  methods: {
    /*
     * Responsible for marking all form element descendents in this form container
     * as touched, or not touched, depending on what we're achieving in validation.
     */
    setFormElementDescendantsTouched(wasTouched) {
      this.getFormElementDescendants.forEach((descendant) => {
        this.$store.dispatch('formData/setElementTouched', {
          page: this.page,
          wasTouched,
          elementId: descendant.id,
        })
      })
    },
    /*
     * Responsible for resetting a form container's elements, depending on
     * value of the reset_initial_values_post_submission property. If true, the
     * form elements will be reset to their initial values, if false, they will
     * be left intact.
     */
    resetFormContainerElements() {
      if (this.element.reset_initial_values_post_submission) {
        this.getFormElementDescendants.forEach((element) => {
          const elementType = this.$registry.get('element', element.type)
          const initialValue = elementType.getInitialFormDataValue(
            element,
            this.applicationContext
          )
          const payload = {
            touched: false,
            value: initialValue,
            type: elementType.formDataType,
            isValid: elementType.isValid(element, initialValue),
          }
          this.$store.dispatch('formData/setFormData', {
            page: this.page,
            payload,
            elementId: element.id,
          })
        })
      } else {
        // If we don't want to reset to initial values, we still
        // want to mark the form elements as not touched.
        this.setFormElementDescendantsTouched(false)
      }
    },
    /*
     * Responsible for validating the form container's elements and submitting the form.
     */
    validateAndSubmitEvent() {
      this.setFormElementDescendantsTouched(true)
      if (!this.formElementChildrenAreInvalid) {
        this.fireSubmitEvent()
        this.resetFormContainerElements()
      }
    },
    showAddElementModal() {
      this.$refs.addElementModal.show({
        placeInContainer: null,
        parentElementId: this.element.id,
      })
    },
  },
}
</script>
