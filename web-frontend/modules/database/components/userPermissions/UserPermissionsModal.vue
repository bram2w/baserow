<template>
  <Modal
    ref="modal"
    :title="$t('userPermissions.title')"
    :content-scrollable="false"
    large
    @hidden="$emit('hidden')"
  >
    <div class="user-permissions-modal">
      <!-- Header with actions -->
      <div class="user-permissions-modal__header">
        <div class="user-permissions-modal__header-info">
          <h2 class="user-permissions-modal__table-name">
            {{ table.name }}
          </h2>
          <p class="user-permissions-modal__description">
            {{ $t('userPermissions.description') }}
          </p>
        </div>
        <div class="user-permissions-modal__header-actions">
          <Button
            v-if="canManage"
            type="primary"
            icon="iconoir-plus"
            :loading="loading"
            @click="openCreateRuleModal"
          >
            {{ $t('userPermissions.addUser') }}
          </Button>
          <Button
            type="secondary"
            icon="iconoir-refresh"
            :loading="loadingRules"
            @click="refreshRules"
          >
            {{ $t('userPermissions.refresh') }}
          </Button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="user-permissions-modal__tabs">
        <a
          class="user-permissions-modal__tab"
          :class="{ 'user-permissions-modal__tab--active': activeTab === 'permissions' }"
          @click="activeTab = 'permissions'"
        >
          {{ $t('userPermissions.tabs.permissions') }}
        </a>
        <a
          v-if="canManage"
          class="user-permissions-modal__tab"
          :class="{ 'user-permissions-modal__tab--active': activeTab === 'audit' }"
          @click="activeTab = 'audit'"
        >
          {{ $t('userPermissions.tabs.auditLog') }}
        </a>
      </div>

      <!-- Content -->
      <div class="user-permissions-modal__content">
        <!-- Permissions Tab -->
        <div v-if="activeTab === 'permissions'" class="user-permissions-modal__permissions">
          <!-- Loading state -->
          <div v-if="loadingRules" class="user-permissions-modal__loading">
            <div class="loading"></div>
          </div>

          <!-- Empty state -->
          <div
            v-else-if="rules.length === 0"
            class="user-permissions-modal__empty"
          >
            <div class="user-permissions-modal__empty-icon">
              <i class="iconoir-lock"></i>
            </div>
            <h3>{{ $t('userPermissions.empty.title') }}</h3>
            <p>{{ $t('userPermissions.empty.description') }}</p>
            <Button
              v-if="canManage"
              type="primary"
              @click="openCreateRuleModal"
            >
              {{ $t('userPermissions.empty.action') }}
            </Button>
          </div>

          <!-- Rules list -->
          <div v-else class="user-permissions-modal__rules">
            <UserPermissionRule
              v-for="rule in rules"
              :key="rule.user.id"
              :rule="rule"
              :table="table"
              :fields="fields"
              :can-manage="canManage"
              @update="updateRule"
              @delete="revokeRule"
              @view-details="viewRuleDetails"
            />
          </div>
        </div>

        <!-- Audit Log Tab -->
        <div v-else-if="activeTab === 'audit'" class="user-permissions-modal__audit">
          <UserPermissionAuditLog
            :table="table"
            :audit-logs="auditLogs"
            :loading="loadingAuditLogs"
            @refresh="loadAuditLogs"
          />
        </div>
      </div>
    </div>

    <!-- Create Rule Modal -->
    <CreateUserPermissionRuleModal
      ref="createRuleModal"
      :table="table"
      :fields="fields"
      :available-users="assignableUsers"
      @created="onRuleCreated"
    />

    <!-- Edit Rule Modal -->
    <EditUserPermissionRuleModal
      ref="editRuleModal"
      :rule="selectedRule"
      :table="table"
      :fields="fields"
      @updated="onRuleUpdated"
    />

    <!-- Rule Details Modal -->
    <UserPermissionRuleDetailsModal
      ref="ruleDetailsModal"
      :rule="selectedRule"
      :table="table"
      :fields="fields"
    />
  </Modal>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'

import Modal from '@baserow/modules/core/components/Modal'
import Button from '@baserow/modules/core/components/Button'
import UserPermissionRule from '@baserow/modules/database/components/userPermissions/UserPermissionRule'
import UserPermissionAuditLog from '@baserow/modules/database/components/userPermissions/UserPermissionAuditLog'
import CreateUserPermissionRuleModal from '@baserow/modules/database/components/userPermissions/CreateUserPermissionRuleModal'
import EditUserPermissionRuleModal from '@baserow/modules/database/components/userPermissions/EditUserPermissionRuleModal'
import UserPermissionRuleDetailsModal from '@baserow/modules/database/components/userPermissions/UserPermissionRuleDetailsModal'

export default {
  name: 'UserPermissionsModal',
  components: {
    Modal,
    Button,
    UserPermissionRule,
    UserPermissionAuditLog,
    CreateUserPermissionRuleModal,
    EditUserPermissionRuleModal,
    UserPermissionRuleDetailsModal,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      activeTab: 'permissions',
      selectedRule: null,
    }
  },
  computed: {
    ...mapState('userPermissions', [
      'rules',
      'auditLogs',
      'loading',
      'loadingRules',
      'loadingAuditLogs',
      'canManage',
    ]),
    ...mapGetters('userPermissions', ['getAssignableUsers']),
    assignableUsers() {
      return this.getAssignableUsers
    },
  },
  async mounted() {
    await this.initializeData()
  },
  methods: {
    ...mapActions('userPermissions', [
      'fetchRules',
      'fetchAuditLogs',
      'checkManagePermissions',
      'fetchAvailableUsers',
      'updateRule',
      'revokeRule',
      'clearState',
    ]),
    show() {
      this.$refs.modal.show()
    },
    hide() {
      this.$refs.modal.hide()
    },
    async initializeData() {
      try {
        // Check if user can manage permissions
        await this.checkManagePermissions(this.table.id)
        
        // Fetch available users for assignment
        if (this.canManage) {
          await this.fetchAvailableUsers(this.table.id)
        }
        
        // Load rules and audit logs
        await Promise.all([
          this.refreshRules(),
          this.canManage ? this.loadAuditLogs() : Promise.resolve(),
        ])
      } catch (error) {
        console.error('Failed to initialize user permissions data:', error)
        this.$store.dispatch('toast/error', {
          title: this.$t('userPermissions.errors.initializationFailed'),
          message: error.response?.data?.detail || error.message,
        })
      }
    },
    async refreshRules() {
      try {
        await this.fetchRules(this.table.id)
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('userPermissions.errors.fetchRulesFailed'),
          message: error.response?.data?.detail || error.message,
        })
      }
    },
    async loadAuditLogs() {
      try {
        await this.fetchAuditLogs({
          tableId: this.table.id,
          params: { page_size: 50 }
        })
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('userPermissions.errors.fetchAuditLogsFailed'),
          message: error.response?.data?.detail || error.message,
        })
      }
    },
    openCreateRuleModal() {
      this.$refs.createRuleModal.show()
    },
    async onRuleCreated(rule) {
      this.$store.dispatch('toast/success', {
        title: this.$t('userPermissions.success.ruleCreated'),
        message: this.$t('userPermissions.success.ruleCreatedMessage', {
          userName: rule.user.first_name || rule.user.email,
          role: this.$t(`userPermissions.roles.${rule.role}`)
        }),
      })
      
      // Refresh data
      await this.refreshRules()
      if (this.canManage) {
        await this.loadAuditLogs()
      }
    },
    async onRuleUpdated(rule) {
      this.$store.dispatch('toast/success', {
        title: this.$t('userPermissions.success.ruleUpdated'),
        message: this.$t('userPermissions.success.ruleUpdatedMessage', {
          userName: rule.user.first_name || rule.user.email,
        }),
      })
      
      // Refresh audit logs
      if (this.canManage) {
        await this.loadAuditLogs()
      }
    },
    async revokeRule(rule) {
      try {
        await this.revokeRule({
          tableId: this.table.id,
          userId: rule.user.id,
        })
        
        this.$store.dispatch('toast/success', {
          title: this.$t('userPermissions.success.ruleRevoked'),
          message: this.$t('userPermissions.success.ruleRevokedMessage', {
            userName: rule.user.first_name || rule.user.email,
          }),
        })
        
        // Refresh audit logs
        if (this.canManage) {
          await this.loadAuditLogs()
        }
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('userPermissions.errors.revokeRuleFailed'),
          message: error.response?.data?.detail || error.message,
        })
      }
    },
    viewRuleDetails(rule) {
      this.selectedRule = rule
      this.$refs.ruleDetailsModal.show()
    },
  },
  beforeDestroy() {
    // Clear state when component is destroyed
    this.clearState()
  },
}
</script>

<style lang="scss" scoped>
@import '@baserow/modules/core/assets/scss/colors';

.user-permissions-modal {
  display: flex;
  flex-direction: column;
  height: 600px;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 20px 24px;
    border-bottom: 1px solid $color-neutral-200;

    &-info {
      flex: 1;
    }

    &-actions {
      display: flex;
      gap: 8px;
      margin-left: 16px;
    }
  }

  &__table-name {
    margin: 0 0 8px;
    font-size: 18px;
    font-weight: 600;
    color: $color-neutral-900;
  }

  &__description {
    margin: 0;
    color: $color-neutral-600;
    font-size: 14px;
  }

  &__tabs {
    display: flex;
    border-bottom: 1px solid $color-neutral-200;
    padding: 0 24px;
  }

  &__tab {
    padding: 12px 16px;
    font-weight: 500;
    color: $color-neutral-600;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      color: $color-primary-600;
    }

    &--active {
      color: $color-primary-600;
      border-bottom-color: $color-primary-600;
    }
  }

  &__content {
    flex: 1;
    overflow: hidden;
  }

  &__permissions,
  &__audit {
    height: 100%;
    overflow-y: auto;
  }

  &__loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    padding: 40px;

    &-icon {
      font-size: 48px;
      color: $color-neutral-400;
      margin-bottom: 16px;
    }

    h3 {
      margin: 0 0 8px;
      color: $color-neutral-700;
    }

    p {
      margin: 0 0 24px;
      color: $color-neutral-500;
    }
  }

  &__rules {
    padding: 16px 24px;
  }
}
</style>