<template>
  <Modal>
    <h2 class="box__title">{{ $t('addElementModal.title') }}</h2>
    <FormInput
      v-model="search"
      class="margin-bottom-2"
      :placeholder="$t('addElementModal.searchPlaceholder')"
      icon-right="search"
    />
    <div class="add-element-modal__element-cards">
      <AddElementCard
        v-for="elementType in elementTypes"
        :key="elementType.getType()"
        :element-type="elementType"
        :loading="addingElementType === elementType.getType()"
        :disabled="isCardDisabled(elementType)"
        @click="addElement(elementType)"
      />
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import AddElementCard from '@baserow/modules/builder/components/elements/AddElementCard'
import { isSubstringOfStrings } from '@baserow/modules/core/utils/string'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { mapActions } from 'vuex'

export default {
  name: 'AddElementModal',
  components: { AddElementCard },
  mixins: [modal],
  props: {
    page: {
      type: Object,
      required: true,
    },
    elementTypesAllowed: {
      type: Array,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      search: '',
      placeInContainer: null,
      beforeId: null,
      parentElementId: null,
      addingElementType: null,
    }
  },
  computed: {
    elementTypes() {
      const elementTypesAll =
        this.elementTypesAllowed ||
        Object.values(this.$registry.getAll('element'))
      return elementTypesAll.filter((elementType) =>
        isSubstringOfStrings(
          [elementType.name, elementType.description],
          this.search
        )
      )
    },
  },
  methods: {
    isCardDisabled(elementType) {
      return (
        this.addingElementType !== null &&
        elementType.getType() !== this.addingElementType
      )
    },
    ...mapActions({
      actionCreateElement: 'element/create',
    }),

    show({ placeInContainer, beforeId, parentElementId } = {}, ...args) {
      this.placeInContainer = placeInContainer
      this.beforeId = beforeId
      this.parentElementId = parentElementId
      modal.methods.show.bind(this)(...args)
    },
    async addElement(elementType) {
      this.addingElementType = elementType.getType()
      const configuration = this.parentElementId
        ? {
            parent_element_id: this.parentElementId,
            place_in_container: this.placeInContainer,
          }
        : null

      try {
        await this.actionCreateElement({
          page: this.page,
          elementType: elementType.getType(),
          beforeId: this.beforeId,
          configuration,
        })

        this.$emit('element-added')
        this.hide()
      } catch (error) {
        notifyIf(error)
      }
      this.addingElementType = null
    },
  },
}
</script>
