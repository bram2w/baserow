<template>
  <div class="select-list-footer select-list-footer--single">
    <a
      class="button"
      :class="{ disabled: !inviteEnabled }"
      @click="inviteEnabled ? $emit('invite') : null"
      >{{ $t('memberAssignmentModalFooter.invite', { count }) }}
    </a>
  </div>
</template>

<script>
export default {
  name: 'MemberAssignmentModalFooter',
  props: {
    count: {
      type: Number,
      required: true,
    },
  },
  computed: {
    inviteEnabled() {
      return this.count !== 0
    },
  },
}
</script>
