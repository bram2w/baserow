<template>
  <div>
    <a
      class="context__menu-item-link"
      @click="
        () => {
          if (deactivated) {
            $refs.premiumModal.show()
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
    <PremiumModal
      ref="premiumModal"
      :name="$t('memberRolesDatabaseContexItem.additionalRoles')"
      :workspace="application.workspace"
    ></PremiumModal>
  </div>
</template>

<script>
import MemberRolesModal from '@baserow_enterprise/components/member-roles/MemberRolesModal'
import EnterpriseFeatures from '@baserow_enterprise/features'
import PremiumModal from '@baserow_premium/components/PremiumModal'

export default {
  name: 'MemberRolesDatabaseContextItem',
  components: { MemberRolesModal, PremiumModal },
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
