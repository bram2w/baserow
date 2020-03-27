<template>
  <li
    class="select-item"
    :class="{
      active: group._.selected,
      'select-item-loading': group._.loading
    }"
  >
    <div class="loading-overlay"></div>
    <a class="select-item-link" @click="selectGroup(group)">
      <Editable
        ref="rename"
        :value="group.name"
        @change="renameGroup(group, $event)"
      ></Editable>
    </a>
    <a
      ref="contextLink"
      class="select-item-options"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
    >
      <i class="fas fa-ellipsis-v"></i>
    </a>
    <Context ref="context">
      <ul class="context-menu">
        <li>
          <a @click="enableRename()">
            <i class="context-menu-icon fas fa-fw fa-pen"></i>
            Rename group
          </a>
        </li>
        <li>
          <a @click="deleteGroup(group)">
            <i class="context-menu-icon fas fa-fw fa-trash"></i>
            Delete group
          </a>
        </li>
      </ul>
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'GroupsContextItem',
  props: {
    group: {
      type: Object,
      required: true
    }
  },
  methods: {
    setLoading(group, value) {
      this.$store.dispatch('group/setItemLoading', { group, value: value })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameGroup(group, event) {
      this.setLoading(group, true)

      try {
        await this.$store.dispatch('group/update', {
          group,
          values: {
            name: event.value
          }
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'group')
      }

      this.setLoading(group, false)
    },
    async selectGroup(group) {
      this.setLoading(group, true)

      try {
        await this.$store.dispatch('group/select', group)
        this.$emit('selected')
      } catch (error) {
        notifyIf(error, 'group')
      }

      this.setLoading(group, false)
    },
    async deleteGroup(group) {
      this.$refs.context.hide()
      this.setLoading(group, true)

      try {
        await this.$store.dispatch('group/delete', group)
      } catch (error) {
        notifyIf(error, 'group')
      }

      this.setLoading(group, false)
    }
  }
}
</script>
