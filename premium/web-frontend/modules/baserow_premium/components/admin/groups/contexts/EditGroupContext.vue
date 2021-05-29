<template>
  <Context>
    <template v-if="Object.keys(group).length > 0">
      <ul class="context__menu">
        <li>
          <a @click.prevent="showDeleteModal">
            <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
            Permanently delete
          </a>
        </li>
      </ul>
      <DeleteGroupModal
        ref="deleteGroupModal"
        :group="group"
        @group-deleted="$emit('group-deleted', $event)"
      ></DeleteGroupModal>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import DeleteGroupModal from '@baserow_premium/components/admin/groups/modals/DeleteGroupModal'

export default {
  name: 'EditUserContext',
  components: { DeleteGroupModal },
  mixins: [context],
  props: {
    group: {
      required: true,
      type: Object,
    },
  },
  methods: {
    showDeleteModal() {
      this.hide()
      this.$refs.deleteGroupModal.show()
    },
  },
}
</script>
