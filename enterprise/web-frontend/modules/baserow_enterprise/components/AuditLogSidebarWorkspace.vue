<template>
  <li
    v-if="hasPermission"
    v-tooltip="deactivated ? $t('auditLogSidebarWorkspace.deactivated') : null"
    class="tree__item"
    :class="{
      'tree__item--loading': loading,
      'tree__action--disabled': deactivated,
      'tree__action--deactivated': deactivated,
      active: $route.matched.some(({ name }) => name === 'workspace-audit-log'),
    }"
  >
    <div class="tree__action">
      <nuxt-link
        :event="deactivated || !hasPermission ? null : 'click'"
        class="tree__link"
        :to="{
          name: 'workspace-audit-log',
          params: { workspaceId: workspace.id },
        }"
      >
        <i class="tree__icon tree__icon--type fas fa-history"></i>
        {{ $t('auditLogSidebarWorkspace.title') }}
      </nuxt-link>
    </div>
  </li>
</template>

<script>
import EnterpriseFeatures from '@baserow_enterprise/features'

export default {
  name: 'AuditLogSidebarWorkspace',
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
      return !this.$hasFeature(EnterpriseFeatures.AUDIT_LOG)
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
