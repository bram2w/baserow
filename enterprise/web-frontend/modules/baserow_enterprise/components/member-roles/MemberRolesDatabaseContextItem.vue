<template>
  <div>
    <a
      class="context__menu-item-link"
      @click="
        () => {
          if (deactivated) {
            $refs.enterpriseModal.show()
          } else {
            $refs.memberRolesModal.show()
          }
        }
      "
    >
      <i class="context__menu-item-icon iconoir-community"></i>
      {{ $t('memberRolesDatabaseContexItem.label') }}
      <div v-if="deactivated" class="deactivated-label">
        <i class="iconoir-lock"></i>
      </div>
    </a>
    <MemberRolesModal ref="memberRolesModal" :database="application" />
    <EnterpriseModal
      ref="enterpriseModal"
      :name="$t('memberRolesDatabaseContexItem.additionalRoles')"
      :workspace="application.workspace"
    ></EnterpriseModal>
  </div>
</template>

<script>
import MemberRolesModal from '@baserow_enterprise/components/member-roles/MemberRolesModal'
import EnterpriseFeatures from '@baserow_enterprise/features'
import EnterpriseModal from '@baserow_enterprise/components/EnterpriseModal'

export default {
  name: 'MemberRolesDatabaseContextItem',
  components: { MemberRolesModal, EnterpriseModal },
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  computed: {
    deactivated() {
      return !this.$hasFeature(
        EnterpriseFeatures.RBAC,
        this.application.workspace.id
      )
    },
  },
}
</script>
