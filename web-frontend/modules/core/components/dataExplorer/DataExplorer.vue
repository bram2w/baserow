<template>
  <Context
    overflow-scroll
    max-height-if-outside-viewport
    :hide-on-click-outside="false"
    class="data-explorer"
    @shown="onShow"
  >
    <div v-if="loading" class="context--loading">
      <div class="loading"></div>
    </div>
    <template v-else>
      <SelectSearch
        v-model="search"
        :placeholder="$t('action.search')"
        class="margin-bottom-1"
      ></SelectSearch>
      <RootNode
        v-for="node in matchingNodes"
        :key="node.identifier"
        :node="node"
        :node-selected="nodeSelected"
        :open-nodes="openNodes"
        @node-selected="$emit('node-selected', $event)"
        @toggle="toggleNode"
      >
      </RootNode>
      <div v-if="matchingNodes.length === 0" class="context__description">
        {{ $t('dataExplorer.emptyText') }}
      </div>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import SelectSearch from '@baserow/modules/core/components/SelectSearch'
import RootNode from '@baserow/modules/core/components/dataExplorer/RootNode'
import _ from 'lodash'

export default {
  name: 'DataExplorer',
  components: { SelectSearch, RootNode },
  mixins: [context],
  props: {
    nodes: {
      type: Array,
      required: false,
      default: () => [],
    },
    nodeSelected: {
      type: String,
      required: false,
      default: null,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      search: null,
      debounceSearch: null,
      debouncedSearch: null,
      // A map of open node paths
      openNodes: new Set(),
    }
  },
  computed: {
    isSearching() {
      return Boolean(this.debouncedSearch)
    },
    matchingPaths() {
      if (!this.isSearching) {
        return new Set()
      } else {
        return this.matchesSearch(this.nodes, this.debouncedSearch)
      }
    },
    matchingNodes() {
      if (!this.isSearching) {
        return this.nodes
      } else {
        return this.filterNodes(
          this.nodes,
          (node, path) => path === '' || this.matchingPaths.has(path)
        )
      }
    },
  },
  watch: {
    /**
     * Debounces the actual search to prevent perf issues
     */
    search(value) {
      clearTimeout(this.debounceSearch)
      this.debounceSearch = setTimeout(() => {
        this.debouncedSearch = value
      }, 300)
    },
    matchingPaths(value) {
      this.openNodes = value
    },
    nodeSelected: {
      handler(value) {
        if (value !== null) {
          this.toggleNode(value, true)
        }
      },
      immediate: true,
    },
  },
  methods: {
    /**
     * Resets state on show context
     */
    onShow() {
      this.search = null
      this.openNodes = new Set()
    },
    /**
     * Given a dotted path, returns a list of prefixes and the given path.
     * @param {String} path the path we want the ancestors for.
     */
    getPathAndParents(path) {
      return _.toPath(path).map((item, index, pathParts) =>
        pathParts.slice(0, index + 1).join('.')
      )
    },
    /**
     * Returns a Set of leaf nodes path that match the search term (and their parents).
     * @param {Array} nodes Nodes tree.
     * @param {String} parentPath Path of the current nodes.
     * @returns A Set of path of nodes that match the search term
     */
    matchesSearch(nodes, search, parentPath = []) {
      const searchSanitised = search.trim().toLowerCase()

      return (nodes || []).reduce((acc, subNode) => {
        const subNodePath = [...parentPath, subNode.identifier]

        if (subNode.nodes) {
          // It's not a leaf
          const subSubNodes = this.matchesSearch(
            subNode.nodes,
            search,
            subNodePath
          )
          acc = new Set([...acc, ...subSubNodes])
        } else {
          // It's a leaf we check if the name match the search
          const nodeNameSanitised = subNode.name.trim().toLowerCase()

          if (nodeNameSanitised.includes(searchSanitised)) {
            // We also add the parents of the node
            acc = new Set([...acc, ...this.getPathAndParents(subNodePath)])
          }
        }
        return acc
      }, new Set())
    },
    /**
     * Filters the nodes according to the given predicate. The predicate receives the
     * node itself and the path of the node.
     * @param {Array} nodes Node tree to filter.
     * @param {Function} predicate Should return true if the node should be kept.
     * @param {Array<String>} path Current nodes path part list.
     */
    filterNodes(nodes, predicate, path = []) {
      const result = (nodes || [])
        .filter((node) => predicate(node, [...path, node.identifier].join('.')))
        .map((node) => ({
          ...node,
          nodes: this.filterNodes(node.nodes, predicate, [
            ...path,
            node.identifier,
          ]),
        }))
      return result
    },
    /**
     * Toggles a node state
     * @param {string} path to open/close.
     * @param {Boolean} forceOpen if we want to open the node anyway.
     */
    toggleNode(path, forceOpen = false) {
      const shouldOpenNode = forceOpen || !this.openNodes.has(path)

      if (shouldOpenNode) {
        // Open all parents as well
        this.openNodes = new Set([
          ...this.openNodes,
          ...this.getPathAndParents(path),
        ])
      } else {
        const newOpenNodes = new Set(this.openNodes)
        newOpenNodes.delete(path)
        this.openNodes = newOpenNodes
      }

      this.$emit('node-toggled')
    },
  },
}
</script>
