<template>
  <Modal>
    <MemberSelectionList
      ref="memberSelectionList"
      class="margin-top-2"
      :members="members"
      @invite="storeSelectedMembers"
    />
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'
import MemberSelectionList from '@baserow/modules/core/components/group/MemberSelectionList'

export default {
  name: 'MemberAssignmentModal',
  components: { MemberSelectionList },
  mixins: [Modal],
  props: {
    members: {
      type: Array,
      required: true,
    },
  },
  methods: {
    storeSelectedMembers(membersSelected) {
      this.$emit('invite', membersSelected)
      this.hide()
    },
  },
}
</script>
