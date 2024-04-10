<template>
  <div>
    <div class="context__menu-item">
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
    </div>
    <MemberRolesModal
      ref="memberRolesModal"
      :database="database"
      :table="table"
    />
    <PremiumModal
      ref="premiumModal"
      :name="$t('memberRolesTableContexItem.additionalRoles')"
      :workspace="database.workspace"
    ></PremiumModal>
  </div>
</template>

<script>
import MemberRolesModal from '@baserow_enterprise/components/member-roles/MemberRolesModal'
import EnterpriseFeatures from '@baserow_enterprise/features'
import PremiumModal from '@baserow_premium/components/PremiumModal'

export default {
  name: 'MemberRolesTableContextItem',
  components: { MemberRolesModal, PremiumModal },
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
  computed: {
    deactivated() {
      return !this.$hasFeature(
        EnterpriseFeatures.RBAC,
        this.database.workspace.id
      )
    },
  },
}
</script>
