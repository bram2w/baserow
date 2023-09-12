<template>
  <NodeViewWrapper as="span" class="get-formula-component">
    {{ pathParts.dataProvider }}
    <template v-for="(part, index) in pathParts.parts">
      <i :key="index" class="get-formula-component__caret fas fa-angle-right">
      </i>
      {{ part }}
    </template>
    <a class="get-formula-component__remove" @click="deleteNode">
      <i class="fas fa-times"></i>
    </a>
  </NodeViewWrapper>
</template>

<script>
import { NodeViewWrapper } from '@tiptap/vue-2'
import formulaComponent from '@baserow/modules/core/mixins/formulaComponent'
import _ from 'lodash'

export default {
  name: 'GetFormulaComponent',
  components: {
    NodeViewWrapper,
  },
  mixins: [formulaComponent],
  computed: {
    path() {
      return this.node.attrs.path
    },
    pathParts() {
      const [dataProvider, ...parts] = _.toPath(this.path)
      const dataProviderType = this.$registry.get(
        'builderDataProvider',
        dataProvider
      )

      return {
        dataProvider: dataProviderType.name,
        parts,
      }
    },
  },
}
</script>
