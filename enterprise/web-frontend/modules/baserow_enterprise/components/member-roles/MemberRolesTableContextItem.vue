<template>
  <div>
    <div class="context__menu-item" @click="() => $refs.modal.show()">
      <a class="context__menu-item-link">
        <i class="context__menu-item-icon iconoir-community"></i
        >{{ $t('memberRolesTableContexItem.label') }}</a
      >
    </div>
    <MemberRolesModal ref="modal" :database="database" :table="table" />
  </div>
</template>

<script>
import MemberRolesModal from '@baserow_enterprise/components/member-roles/MemberRolesModal'

export default {
  name: 'MemberRolesTableContextItem',
  components: { MemberRolesModal },
  props: {
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
}
</script>
