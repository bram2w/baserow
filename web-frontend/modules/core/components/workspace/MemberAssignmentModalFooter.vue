<template>
  <div class="row">
    <div class="col col-6">
      <a
        v-if="toggleEnabled"
        class="button button--ghost"
        @click="$emit('toggle-select-all')"
        >{{ getToggleLabel }}</a
      >
    </div>
    <div class="col col-6 align-right">
      <a
        class="button"
        :class="{ disabled: !inviteEnabled }"
        @click="inviteEnabled ? $emit('invite') : null"
        >{{
          $t('memberAssignmentModalFooter.invite', { selectedMembersCount })
        }}
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MemberAssignmentModalFooter',
  props: {
    filteredMembersCount: {
      type: Number,
      required: true,
    },
    selectedMembersCount: {
      type: Number,
      required: true,
    },
    allFilteredMembersSelected: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    toggleEnabled() {
      return this.filteredMembersCount !== 0
    },
    inviteEnabled() {
      return this.selectedMembersCount !== 0
    },
    getToggleLabel() {
      return this.allFilteredMembersSelected
        ? this.$t('memberAssignmentModalFooter.deselectAll')
        : this.$t('memberAssignmentModalFooter.selectAll')
    },
  },
}
</script>
