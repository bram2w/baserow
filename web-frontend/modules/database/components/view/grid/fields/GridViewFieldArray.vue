<template>
  <div class="grid-view__cell active">
    <FunctionalGridViewFieldArray
      :field="field"
      :value="value"
      :selected="selected"
      v-on="$listeners"
      @show="showModal"
    ></FunctionalGridViewFieldArray>
    <component
      :is="modalComponent"
      v-if="needsModal"
      ref="modal"
      :read-only="true"
      :value="value"
    ></component>
  </div>
</template>

<script>
import FunctionalGridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray'
import gridField from '@baserow/modules/database/mixins/gridField'
import FileFieldModal from '@baserow/modules/database/components/field/FileFieldModal.vue'
import { isElement } from '@baserow/modules/core/utils/dom'

export default {
  name: 'GridViewFieldArray',
  components: { FileFieldModal, FunctionalGridViewFieldArray },
  mixins: [gridField],
  props: {
    selected: {
      type: Boolean,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  computed: {
    subType() {
      return this.$registry.get('formula_type', this.field.array_formula_type)
    },
    modalComponent() {
      return this.subType.getExtraModal()
    },
    needsModal() {
      return this.modalComponent !== null
    },
  },
  methods: {
    showModal() {
      this.$refs.modal?.show()
    },
    canUnselectByClickingOutside(event) {
      return (
        !this.needsModal ||
        ((!this.$refs.modal ||
          !isElement(this.$refs.modal.$el, event.target)) &&
          !isElement(this.$refs.modal.$el, event.target))
      )
    },
  },
}
</script>
