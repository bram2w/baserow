<template>
  <div>
    <div @click="() => $refs.modal.show()">
      <a>
        <i class="context__menu-icon fas fa-fw fa-users"></i
        >{{ $t('memberRolesDatabaseContexItem.label') }}</a
      >
    </div>
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
