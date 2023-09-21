<template functional>
  <div
    :data-identifier="props.node.identifier"
    class="node"
    :class="{ 'node--first-indentation': props.indentation === 0 }"
  >
    <div
      class="node__content"
      :class="{
        'node__content--selected': props.nodeSelected === props.path,
      }"
      @click="$options.methods.click(props.node, props.path, listeners)"
    >
      <div class="node__content-name">
        <i
          class="node__icon"
          :class="`fas fa-${$options.methods.getIcon(
            props.node,
            props.openNodes.has(props.path)
          )}`"
        ></i>
        {{ props.node.name }}
      </div>
      <i
        v-if="props.nodeSelected === props.path"
        class="node__selected fas fa-check-circle"
      ></i>
    </div>

    <div v-if="props.openNodes.has(props.path)">
      <Node
        v-for="subNode in props.node.nodes || []"
        :key="subNode.identifier"
        :node="subNode"
        :open-nodes="props.openNodes"
        :node-selected="props.nodeSelected"
        :indentation="props.indentation + 1"
        :path="`${props.path}.${subNode.identifier}`"
        @click="listeners.click && listeners.click($event)"
        @toggle="listeners.toggle && listeners.toggle($event)"
      ></Node>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Node',
  props: {
    node: {
      type: Object,
      required: true,
    },
    openNodes: {
      type: Set,
      required: true,
    },
    path: {
      type: String,
      required: true,
    },
    indentation: {
      type: Number,
      required: false,
      default: 0,
    },
    nodeSelected: {
      type: String,
      required: false,
      default: null,
    },
  },
  methods: {
    click(node, path, listeners) {
      if (node.nodes?.length > 0 && listeners.toggle) {
        listeners.toggle(path)
      } else if (listeners.click) {
        listeners.click({
          path,
          node,
        })
      }
    },

    getIcon(node, isOpen) {
      if (!node.nodes?.length || node.nodes?.length < 1) {
        return node.icon
      }

      return isOpen ? 'caret-down' : 'caret-right'
    },
  },
}
</script>
