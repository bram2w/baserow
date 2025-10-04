<template>
  <Modal
    ref="modal"
    :title="$t('userPermissions.ruleDetails.title')"
    large
    @hidden="$emit('hidden')"
  >
    <div v-if="rule" class="user-permission-details">
      <!-- User Info Section -->
      <div class="user-permission-details__section">
        <h3 class="user-permission-details__section-title">
          {{ $t('userPermissions.ruleDetails.userInfo') }}
        </h3>
        <div class="user-permission-details__user">
          <Avatar
            :initials="userInitials"
            :name="userName"
            size="large"
          />
          <div class="user-permission-details__user-info">
            <h4 class="user-permission-details__user-name">{{ userName }}</h4>
            <p class="user-permission-details__user-email">{{ rule.user.email }}</p>
            <div class="user-permission-details__role">
              <Badge
                :color="getRoleColor(rule.role)"
                :icon="getRoleIcon(rule.role)"
              >
                {{ $t(`userPermissions.roles.${rule.role}`) }}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <!-- Effective Permissions Section -->
      <div class="user-permission-details__section">
        <h3 class="user-permission-details__section-title">
          {{ $t('userPermissions.ruleDetails.effectivePermissions') }}
        </h3>
        <div class="user-permission-details__permissions-grid">
          <div
            v-for="permission in permissions"
            :key="permission.key"
            class="user-permission-details__permission"
            :class="{ 'user-permission-details__permission--allowed': permission.allowed }"
          >
            <i :class="permission.icon" class="user-permission-details__permission-icon"></i>
            <div class="user-permission-details__permission-info">
              <h5 class="user-permission-details__permission-title">{{ permission.label }}</h5>
              <p class="user-permission-details__permission-description">{{ permission.description }}</p>
            </div>
            <div class="user-permission-details__permission-status">
              <i :class="permission.allowed ? 'iconoir-check' : 'iconoir-cancel'"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- Row Filters Section -->
      <div v-if="hasRowFilters" class="user-permission-details__section">
        <h3 class="user-permission-details__section-title">
          {{ $t('userPermissions.ruleDetails.rowFilters') }}
        </h3>
        <div class="user-permission-details__filters">
          <div
            v-for="(value, field) in rule.row_filter"
            :key="field"
            class="user-permission-details__filter"
          >
            <div class="user-permission-details__filter-field">{{ field }}</div>
            <div class="user-permission-details__filter-operator">=</div>
            <div class="user-permission-details__filter-value">{{ value }}</div>
          </div>
        </div>
        <div class="user-permission-details__filter-note">
          <i class="iconoir-info-circle"></i>
          <span>{{ $t('userPermissions.ruleDetails.filterNote') }}</span>
        </div>
      </div>

      <!-- Field Permissions Section -->
      <div v-if="hasFieldPermissions" class="user-permission-details__section">
        <h3 class="user-permission-details__section-title">
          {{ $t('userPermissions.ruleDetails.fieldPermissions') }}
        </h3>
        <div class="user-permission-details__field-permissions">
          <div
            v-for="fieldPerm in rule.field_permissions"
            :key="fieldPerm.field.id"
            class="user-permission-details__field-permission"
          >
            <div class="user-permission-details__field-info">
              <i :class="getFieldIcon(fieldPerm.field)" class="user-permission-details__field-icon"></i>
              <span class="user-permission-details__field-name">{{ fieldPerm.field.name }}</span>
            </div>
            <div class="user-permission-details__field-permission-level">
              <Badge :color="getPermissionColor(fieldPerm.permission)">
                <i :class="getPermissionIcon(fieldPerm.permission)"></i>
                {{ $t(`userPermissions.fieldPermissions.${fieldPerm.permission}`) }}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <!-- Metadata Section -->
      <div class="user-permission-details__section">
        <h3 class="user-permission-details__section-title">
          {{ $t('userPermissions.ruleDetails.metadata') }}
        </h3>
        <div class="user-permission-details__metadata">
          <div class="user-permission-details__metadata-item">
            <strong>{{ $t('userPermissions.ruleDetails.createdAt') }}:</strong>
            <span>{{ formatDate(rule.created_at) }}</span>
          </div>
          <div class="user-permission-details__metadata-item">
            <strong>{{ $t('userPermissions.ruleDetails.updatedAt') }}:</strong>
            <span>{{ formatDate(rule.updated_at) }}</span>
          </div>
          <div class="user-permission-details__metadata-item">
            <strong>{{ $t('userPermissions.ruleDetails.isActive') }}:</strong>
            <Badge :color="rule.is_active ? 'success' : 'error'">
              {{ rule.is_active ? $t('common.active') : $t('common.inactive') }}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/components/Modal'
import Avatar from '@baserow/modules/core/components/Avatar'
import Badge from '@baserow/modules/core/components/Badge'

export default {
  name: 'UserPermissionRuleDetailsModal',
  components: {
    Modal,
    Avatar,
    Badge,
  },
  props: {
    rule: {
      type: Object,
      default: null,
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
  computed: {
    userName() {
      if (!this.rule) return ''
      return this.rule.user.first_name || 
             this.rule.user.username || 
             this.rule.user.email.split('@')[0]
    },
    userInitials() {
      if (!this.rule) return ''
      if (this.rule.user.first_name) {
        const names = this.rule.user.first_name.split(' ')
        return names.map(name => name.charAt(0).toUpperCase()).join('')
      }
      return this.rule.user.email.charAt(0).toUpperCase()
    },
    hasRowFilters() {
      return this.rule?.row_filter && Object.keys(this.rule.row_filter).length > 0
    },
    hasFieldPermissions() {
      return this.rule?.field_permissions && this.rule.field_permissions.length > 0
    },
    permissions() {
      if (!this.rule) return []
      
      return [
        {
          key: 'read',
          label: this.$t('userPermissions.permissions.read'),
          description: this.$t('userPermissions.permissionDescriptions.read'),
          icon: 'iconoir-eye',
          allowed: this.rule.effective_permissions.can_read,
        },
        {
          key: 'create',
          label: this.$t('userPermissions.permissions.create'),
          description: this.$t('userPermissions.permissionDescriptions.create'),
          icon: 'iconoir-plus',
          allowed: this.rule.effective_permissions.can_create,
        },
        {
          key: 'update',
          label: this.$t('userPermissions.permissions.update'),
          description: this.$t('userPermissions.permissionDescriptions.update'),
          icon: 'iconoir-edit',
          allowed: this.rule.effective_permissions.can_update,
        },
        {
          key: 'delete',
          label: this.$t('userPermissions.permissions.delete'),
          description: this.$t('userPermissions.permissionDescriptions.delete'),
          icon: 'iconoir-trash',
          allowed: this.rule.effective_permissions.can_delete,
        },
      ]
    },
  },
  methods: {
    show() {
      this.$refs.modal.show()
    },
    hide() {
      this.$refs.modal.hide()
    },
    getRoleColor(role) {
      const colors = {
        admin: 'red',
        manager: 'blue',
        coordinator: 'green',
        viewer: 'gray',
      }
      return colors[role] || 'gray'
    },
    getRoleIcon(role) {
      const icons = {
        admin: 'iconoir-crown',
        manager: 'iconoir-user-star',
        coordinator: 'iconoir-user-plus',
        viewer: 'iconoir-user',
      }
      return icons[role] || 'iconoir-user'
    },
    getFieldIcon(field) {
      const iconMap = {
        text: 'iconoir-text',
        long_text: 'iconoir-text-alt',
        number: 'iconoir-hashtag',
        boolean: 'iconoir-check-circle',
        date: 'iconoir-calendar',
        single_select: 'iconoir-list',
        multiple_select: 'iconoir-multi-select',
        file: 'iconoir-attachment',
        url: 'iconoir-link',
        email: 'iconoir-mail',
        phone_number: 'iconoir-phone',
      }
      return iconMap[field.type] || 'iconoir-text'
    },
    getPermissionColor(permission) {
      const colors = {
        hidden: 'error',
        read: 'warning',
        write: 'success',
      }
      return colors[permission] || 'gray'
    },
    getPermissionIcon(permission) {
      const icons = {
        hidden: 'iconoir-eye-off',
        read: 'iconoir-eye',
        write: 'iconoir-edit',
      }
      return icons[permission] || 'iconoir-eye'
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return new Intl.DateTimeFormat(this.$i18n.locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    },
  },
}
</script>

<style lang="scss" scoped>
.user-permission-details {
  &__section {
    margin-bottom: 32px;

    &:last-child {
      margin-bottom: 0;
    }

    &-title {
      margin: 0 0 16px;
      font-size: 16px;
      font-weight: 600;
      color: $color-neutral-900;
      border-bottom: 1px solid $color-neutral-200;
      padding-bottom: 8px;
    }
  }

  &__user {
    display: flex;
    align-items: center;
    gap: 16px;

    &-info {
      flex: 1;
    }

    &-name {
      margin: 0 0 4px;
      font-size: 18px;
      font-weight: 600;
      color: $color-neutral-900;
    }

    &-email {
      margin: 0 0 8px;
      color: $color-neutral-600;
    }
  }

  &__permissions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }

  &__permission {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    border: 1px solid $color-neutral-200;
    border-radius: 8px;
    background: $color-neutral-50;

    &--allowed {
      border-color: $color-success-300;
      background: $color-success-50;

      .user-permission-details__permission-icon {
        color: $color-success-600;
      }
    }

    &-icon {
      font-size: 20px;
      color: $color-neutral-400;
    }

    &-info {
      flex: 1;
    }

    &-title {
      margin: 0 0 2px;
      font-size: 14px;
      font-weight: 600;
      color: $color-neutral-900;
    }

    &-description {
      margin: 0;
      font-size: 12px;
      color: $color-neutral-600;
    }

    &-status {
      i {
        font-size: 18px;
        
        &.iconoir-check {
          color: $color-success-600;
        }
        
        &.iconoir-cancel {
          color: $color-neutral-400;
        }
      }
    }
  }

  &__filters {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__filter {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: $color-neutral-100;
    border-radius: 6px;
    font-family: monospace;
    font-size: 13px;

    &-field {
      color: $color-primary-600;
      font-weight: 600;
    }

    &-operator {
      color: $color-neutral-600;
    }

    &-value {
      color: $color-success-600;
      font-weight: 500;
    }
  }

  &__filter-note {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    padding: 8px 12px;
    background: $color-warning-50;
    border: 1px solid $color-warning-200;
    border-radius: 6px;
    font-size: 12px;
    color: $color-warning-700;

    i {
      color: $color-warning-600;
    }
  }

  &__field-permissions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__field-permission {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border: 1px solid $color-neutral-200;
    border-radius: 6px;
    background: $color-neutral-50;
  }

  &__field-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__field-icon {
    color: $color-neutral-500;
  }

  &__field-name {
    font-weight: 500;
    color: $color-neutral-900;
  }

  &__metadata {
    display: flex;
    flex-direction: column;
    gap: 8px;

    &-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;

      strong {
        min-width: 120px;
        color: $color-neutral-700;
      }

      span {
        color: $color-neutral-900;
      }
    }
  }
}
</style>