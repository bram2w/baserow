<template>
  <div class="root-node">
    <div class="root-node__name">
      {{ node.name }}
    </div>
    <div ref="nodes">
      <Node
        v-for="subNode in sortNodes(node.nodes)"
        :key="subNode.identifier"
        :node="subNode"
        :node-selected="nodeSelected"
        :open-nodes="openNodes"
        :path="`${node.identifier}.${subNode.identifier}`"
        @click="$emit('node-selected', $event)"
        @toggle="$emit('toggle', $event)"
      ></Node>
    </div>
  </div>
</template>

<script>
import Node from '@baserow/modules/core/components/dataExplorer/Node'
import _ from 'lodash'

export default {
  name: 'RootNode',
  components: { Node },
  props: {
    node: {
      type: Object,
      required: true,
    },
    openNodes: {
      type: Set,
      required: true,
    },
    nodeSelected: {
      type: String,
      required: false,
      default: null,
    },
  },
  watch: {
    async nodeSelected(path) {
      if (path === null) {
        return
      }

      // Wait for the nodes to be opened
      await this.$nextTick()

      const element = this.getNodeElementByPath(
        this.$refs.nodes,
        // Remove the first part since it is the root node, and we don't need that
        _.toPath(path).slice(1)
      )

      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    },
  },
  methods: {
    getNodeElementByPath(element, path) {
      const [identifier, ...rest] = path

      const childMatching = [...element.children].find(
        (child) => child.dataset.identifier === identifier
      )

      // We found the final element!
      if (childMatching && rest.length === 0) {
        return childMatching
      }

      // That means we still haven't gone through the whole path
      if (childMatching && rest.length > 0) {
        return this.getNodeElementByPath(childMatching, rest)
      }

      // That means we have gone into a dead end
      if (!childMatching && !element.children.length) {
        return null
      }

      // That means we have to keep searching the children to find the next piece of the
      // path
      return (
        [...element.children]
          .map((child) => this.getNodeElementByPath(child, path))
          .find((e) => e !== null) || null
      )
    },
    sortNodes(nodes) {
      return nodes.sort((a, b) => (a.name > b.name ? 1 : -1))
    },
  },
}
</script>
