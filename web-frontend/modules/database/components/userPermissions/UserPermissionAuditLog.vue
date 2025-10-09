<template>
  <div class="user-permission-audit-log">
    <!-- Header -->
    <div class="user-permission-audit-log__header">
      <h3 class="user-permission-audit-log__title">
        {{ $t('userPermissions.tabs.auditLog') }}
      </h3>
      <Button
        type="secondary"
        size="small"
        icon="iconoir-refresh"
        :loading="loading"
        @click="$emit('refresh')"
      >
        {{ $t('userPermissions.refresh') }}
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="user-permission-audit-log__loading">
      <div class="loading"></div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="auditLogs.length === 0"
      class="user-permission-audit-log__empty"
    >
      <div class="user-permission-audit-log__empty-icon">
        <i class="iconoir-journal"></i>
      </div>
      <h4>{{ $t('userPermissions.auditLog.empty.title') }}</h4>
      <p>{{ $t('userPermissions.auditLog.empty.description') }}</p>
    </div>

    <!-- Audit logs list -->
    <div v-else class="user-permission-audit-log__list">
      <div
        v-for="log in auditLogs"
        :key="log.id"
        class="user-permission-audit-log__item"
      >
        <!-- Action icon and info -->
        <div class="user-permission-audit-log__item-header">
          <div class="user-permission-audit-log__action">
            <i
              class="user-permission-audit-log__action-icon"
              :class="getActionIcon(log.action)"
            ></i>
            <div class="user-permission-audit-log__action-info">
              <h5 class="user-permission-audit-log__action-title">
                {{ getActionTitle(log.action) }}
              </h5>
              <p class="user-permission-audit-log__action-description">
                {{ getActionDescription(log) }}
              </p>
            </div>
          </div>
          
          <!-- Timestamp -->
          <div class="user-permission-audit-log__timestamp">
            <time :datetime="log.created_at" :title="formatFullDate(log.created_at)">
              {{ formatRelativeTime(log.created_at) }}
            </time>
          </div>
        </div>

        <!-- Details -->
        <div
          v-if="log.details && Object.keys(log.details).length > 0"
          class="user-permission-audit-log__details"
        >
          <div class="user-permission-audit-log__details-toggle">
            <a @click="toggleDetails(log.id)">
              <i 
                class="iconoir-nav-arrow-right"
                :class="{ 'iconoir-nav-arrow-down': expandedLogs.includes(log.id) }"
              ></i>
              {{ $t('userPermissions.auditLog.details') }}
            </a>
          </div>
          
          <div
            v-if="expandedLogs.includes(log.id)"
            class="user-permission-audit-log__details-content"
          >
            <div
              v-for="(value, key) in log.details"
              :key="key"
              class="user-permission-audit-log__detail-item"
            >
              <span class="user-permission-audit-log__detail-key">{{ key }}:</span>
              <span class="user-permission-audit-log__detail-value">
                {{ formatDetailValue(value) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Button from '@baserow/modules/core/components/Button'

export default {
  name: 'UserPermissionAuditLog',
  components: {
    Button,
  },
  props: {
    table: {
      type: Object,
      required: true,
    },
    auditLogs: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      expandedLogs: [],
    }
  },
  methods: {
    getActionIcon(action) {
      const icons = {
        granted: 'iconoir-plus-circle',
        modified: 'iconoir-edit-pencil',
        revoked: 'iconoir-trash',
      }
      return icons[action] || 'iconoir-journal'
    },
    getActionTitle(action) {
      return this.$t(`userPermissions.auditLog.actions.${action}`)
    },
    getActionDescription(log) {
      const actorName = log.actor_user?.first_name || 
                        log.actor_user?.username || 
                        log.actor_user?.email || 
                        this.$t('userPermissions.auditLog.unknownUser')
      
      const targetName = log.target_user?.first_name || 
                         log.target_user?.username || 
                         log.target_user?.email || 
                         this.$t('userPermissions.auditLog.unknownUser')

      return this.$t(`userPermissions.auditLog.descriptions.${log.action}`, {
        actorName,
        targetName,
        tableName: this.table.name,
      })
    },
    formatRelativeTime(dateString) {
      const date = new Date(dateString)
      const now = new Date()
      const diffInMs = now - date
      
      const minutes = Math.floor(diffInMs / (1000 * 60))
      const hours = Math.floor(diffInMs / (1000 * 60 * 60))
      const days = Math.floor(diffInMs / (1000 * 60 * 60 * 24))
      
      if (minutes < 1) return this.$t('userPermissions.auditLog.timeAgo.now')
      if (minutes < 60) return this.$t('userPermissions.auditLog.timeAgo.minutes', { count: minutes })
      if (hours < 24) return this.$t('userPermissions.auditLog.timeAgo.hours', { count: hours })
      if (days < 30) return this.$t('userPermissions.auditLog.timeAgo.days', { count: days })
      
      return this.formatFullDate(dateString)
    },
    formatFullDate(dateString) {
      const date = new Date(dateString)
      return new Intl.DateTimeFormat(this.$i18n.locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    },
    formatDetailValue(value) {
      if (typeof value === 'object' && value !== null) {
        return JSON.stringify(value, null, 2)
      }
      return String(value)
    },
    toggleDetails(logId) {
      const index = this.expandedLogs.indexOf(logId)
      if (index >= 0) {
        this.expandedLogs.splice(index, 1)
      } else {
        this.expandedLogs.push(logId)
      }
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@baserow/modules/core/assets/scss/colors';

.user-permission-audit-log {
  height: 100%;
  display: flex;
  flex-direction: column;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid $color-neutral-200;
  }

  &__title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: $color-neutral-900;
  }

  &__loading {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  &__empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 40px;

    &-icon {
      font-size: 48px;
      color: $color-neutral-400;
      margin-bottom: 16px;
    }

    h4 {
      margin: 0 0 8px;
      color: $color-neutral-700;
    }

    p {
      margin: 0;
      color: $color-neutral-500;
    }
  }

  &__list {
    flex: 1;
    overflow-y: auto;
    padding: 16px 24px;
  }

  &__item {
    padding: 16px;
    border: 1px solid $color-neutral-200;
    border-radius: 8px;
    margin-bottom: 12px;
    background: $color-neutral-50;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  &__action {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex: 1;

    &-icon {
      font-size: 20px;
      margin-top: 2px;
      
      &.iconoir-plus-circle {
        color: $color-success-600;
      }
      
      &.iconoir-edit-pencil {
        color: $color-warning-600;
      }
      
      &.iconoir-trash {
        color: $color-error-600;
      }
    }

    &-info {
      flex: 1;
    }

    &-title {
      margin: 0 0 4px;
      font-size: 14px;
      font-weight: 600;
      color: $color-neutral-900;
    }

    &-description {
      margin: 0;
      font-size: 13px;
      color: $color-neutral-600;
      line-height: 1.4;
    }
  }

  &__timestamp {
    font-size: 12px;
    color: $color-neutral-500;
    white-space: nowrap;
    margin-left: 16px;
  }

  &__details {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid $color-neutral-200;

    &-toggle {
      margin-bottom: 8px;
      
      a {
        display: flex;
        align-items: center;
        gap: 6px;
        color: $color-primary-600;
        cursor: pointer;
        font-size: 12px;
        font-weight: 500;
        
        &:hover {
          color: $color-primary-700;
        }

        i {
          transition: transform 0.2s ease;
          font-size: 10px;
        }
      }
    }

    &-content {
      background: $color-neutral-100;
      border-radius: 4px;
      padding: 12px;
    }
  }

  &__detail-item {
    display: flex;
    margin-bottom: 6px;
    font-size: 12px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__detail-key {
    font-weight: 600;
    color: $color-neutral-700;
    margin-right: 8px;
    min-width: 100px;
  }

  &__detail-value {
    color: $color-neutral-800;
    word-break: break-word;
    white-space: pre-wrap;
  }
}
</style>