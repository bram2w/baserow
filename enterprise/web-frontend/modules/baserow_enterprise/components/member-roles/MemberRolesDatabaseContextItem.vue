<template>
  <div>
    <a class="context__menu-item-link" @click="() => $refs.modal.show()">
      <i class="context__menu-item-icon iconoir-community"></i
      >{{ $t('memberRolesDatabaseContexItem.label') }}</a
    >
    <MemberRolesModal ref="modal" :database="application" />
  </div>
</template>

<script>
import MemberRolesModal from '@baserow_enterprise/components/member-roles/MemberRolesModal'

export default {
  name: 'MemberRolesDatabaseContextItem',
  components: { MemberRolesModal },
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
}
</script>
