<template>
  <li
    v-if="hasPermission"
    class="tree__item"
    :class="{
      'tree__item--loading': loading,
      'tree__action--deactivated': deactivated,
      active: $route.matched.some(({ name }) => name === 'workspace-audit-log'),
    }"
  >
    <div class="tree__action">
      <a
        v-if="deactivated"
        href="#"
        class="tree__link"
        @click.prevent="$refs.enterpriseModal.show()"
      >
        <i class="tree__icon tree__icon--type iconoir-lock"></i>
        <span class="tree__link-text">{{
          $t('auditLogSidebarWorkspace.title')
        }}</span>
      </a>
      <nuxt-link
        v-else
        :event="!hasPermission ? null : 'click'"
        class="tree__link"
        :to="{
          name: 'workspace-audit-log',
          params: { workspaceId: workspace.id },
        }"
      >
        <i class="tree__icon tree__icon--type baserow-icon-history"></i>
        <span class="tree__link-text">{{
          $t('auditLogSidebarWorkspace.title')
        }}</span>
      </nuxt-link>
    </div>
    <EnterpriseModal
      ref="enterpriseModal"
      :workspace="workspace"
      :name="$t('auditLogSidebarWorkspace.title')"
    ></EnterpriseModal>
  </li>
</template>

<script>
import EnterpriseFeatures from '@baserow_enterprise/features'
import EnterpriseModal from '@baserow_enterprise/components/EnterpriseModal'

export default {
  name: 'AuditLogSidebarWorkspace',
  components: { EnterpriseModal },
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  computed: {
    deactivated() {
      return !this.$hasFeature(EnterpriseFeatures.AUDIT_LOG, this.workspace.id)
    },
    hasPermission() {
      return this.$hasPermission(
        'workspace.list_audit_log_entries',
        this.workspace,
        this.workspace.id
      )
    },
  },
}
</script>
