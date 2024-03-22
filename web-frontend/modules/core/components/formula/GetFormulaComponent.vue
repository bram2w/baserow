<template>
  <NodeViewWrapper
    as="span"
    class="get-formula-component"
    :class="{
      'get-formula-component--error': isInvalid,
      'get-formula-component--selected': isSelected,
    }"
  >
    <div
      v-tooltip="$t('getFormulaComponent.errorTooltip')"
      tooltip-position="top"
      :hide-tooltip="!isInvalid"
      @click="emitToEditor('data-component-clicked', node)"
    >
      <template v-for="(part, index) in pathParts">
        <i
          v-if="index > 0"
          :key="index"
          class="get-formula-component__caret iconoir-nav-arrow-right"
        />

        {{ part }}
      </template>
      <a class="get-formula-component__remove" @click="deleteNode">
        <i class="iconoir-cancel"></i>
      </a>
    </div>
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
  inject: ['applicationContext'],
  data() {
    return { nodes: [], pathParts: [] }
  },
  computed: {
    isInvalid() {
      return this.findNode(this.nodes, _.toPath(this.path)) === null
    },
    path() {
      return this.node.attrs.path
    },
    isSelected() {
      return this.node.attrs.isSelected
    },
    rawPathParts() {
      return _.toPath(this.path)
    },
    dataProviderType() {
      return this.$registry.get('builderDataProvider', this.rawPathParts[0])
    },
  },
  mounted() {
    if (this.dataProviderType) {
      this.nodes = [this.dataProviderType.getNodes(this.applicationContext)]
      const translatedPathPart = this.rawPathParts.map((_, index) =>
        this.dataProviderType.getPathTitle(
          this.applicationContext,
          this.rawPathParts.slice(0, index + 1)
        )
      )

      translatedPathPart[0] = this.dataProviderType.name
      this.pathParts = translatedPathPart
    }
  },
  methods: {
    findNode(nodes, path) {
      const [identifier, ...rest] = path

      if (!nodes) {
        return null
      }

      const nodeFound = nodes.find((node) => node.identifier === identifier)

      if (!nodeFound) {
        return null
      }

      if (rest.length > 0) {
        return this.findNode(nodeFound.nodes, rest)
      }

      return nodeFound
    },
  },
}
</script>
