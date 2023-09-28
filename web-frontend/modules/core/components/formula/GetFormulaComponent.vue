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
      {{ pathParts.dataProvider }}
      <template v-for="(part, index) in pathParts.parts">
        <i
          :key="index"
          class="get-formula-component__caret iconoir-nav-arrow-right"
        >
        </i>
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
  computed: {
    availableData() {
      return Object.values(this.$registry.getAll('builderDataProvider')).map(
        (dataProvider) => dataProvider.getNodes(this.applicationContext)
      )
    },
    isInvalid() {
      return this.findNode(this.availableData, _.toPath(this.path)) === null
    },
    path() {
      return this.node.attrs.path
    },
    isSelected() {
      return this.node.attrs.isSelected
    },
    pathParts() {
      const [dataProvider, ...parts] = _.toPath(this.path)
      const dataProviderType = this.$registry.get(
        'builderDataProvider',
        dataProvider
      )

      return {
        dataProvider: dataProviderType.name,
        parts: parts.map((part, index) =>
          dataProviderType.pathPartToDisplay(
            this.applicationContext,
            part,
            index + 1
          )
        ),
      }
    },
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
