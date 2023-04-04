<template>
  <Modal>
    <h2 class="box__title">{{ $t('addElementModal.title') }}</h2>
    <InputWithIcon
      v-model="search"
      class="margin-bottom-2"
      :placeholder="$t('addElementModal.searchPlaceholder')"
      icon="search"
    />
    <div class="add-element-modal__element-cards">
      <AddElementCard
        v-for="elementType in elementTypes"
        :key="elementType.getType()"
        :element-type="elementType"
        :loading="addingElementType === elementType.getType()"
        :disabled="isCardDisabled(elementType)"
        @click="$emit('add', elementType)"
      />
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import AddElementCard from '@baserow/modules/builder/components/elements/AddElementCard'
import { isSubstringOfStrings } from '@baserow/modules/core/utils/string'

export default {
  name: 'AddElementModal',
  components: { AddElementCard },
  mixins: [modal],
  props: {
    page: {
      type: Object,
      required: true,
    },
    addingElementType: {
      type: String,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      search: '',
    }
  },
  computed: {
    elementTypes() {
      const allElementTypes = Object.values(this.$registry.getAll('element'))
      return allElementTypes.filter((elementType) =>
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
  },
}
</script>
