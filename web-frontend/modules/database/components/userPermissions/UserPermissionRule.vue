<template>
  <div class="user-permission-rule">
    <!-- User Info -->
    <div class="user-permission-rule__user">
      <Avatar
        :initials="userInitials"
        :name="userName"
        size="medium"
        class="user-permission-rule__avatar"
      />
      <div class="user-permission-rule__user-info">
        <h4 class="user-permission-rule__user-name">{{ userName }}</h4>
        <p class="user-permission-rule__user-email">{{ rule.user.email }}</p>
      </div>
    </div>

    <!-- Role Badge -->
    <div class="user-permission-rule__role">
      <Badge
        :color="getRoleColor(rule.role)"
        :icon="getRoleIcon(rule.role)"
      >
        {{ $t(`userPermissions.roles.${rule.role}`) }}
      </Badge>
    </div>

    <!-- Permissions Summary -->
    <div class="user-permission-rule__permissions">
      <div class="user-permission-rule__permission-item">
        <i
          class="user-permission-rule__permission-icon iconoir-eye"
          :class="{ 'user-permission-rule__permission-icon--allowed': rule.effective_permissions.can_read }"
        ></i>
        <span class="user-permission-rule__permission-label">
          {{ $t('userPermissions.permissions.read') }}
        </span>
      </div>
      <div class="user-permission-rule__permission-item">
        <i
          class="user-permission-rule__permission-icon iconoir-plus"
          :class="{ 'user-permission-rule__permission-icon--allowed': rule.effective_permissions.can_create }"
        ></i>
        <span class="user-permission-rule__permission-label">
          {{ $t('userPermissions.permissions.create') }}
        </span>
      </div>
      <div class="user-permission-rule__permission-item">
        <i
          class="user-permission-rule__permission-icon iconoir-edit"
          :class="{ 'user-permission-rule__permission-icon--allowed': rule.effective_permissions.can_update }"
        ></i>
        <span class="user-permission-rule__permission-label">
          {{ $t('userPermissions.permissions.update') }}
        </span>
      </div>
      <div class="user-permission-rule__permission-item">
        <i
          class="user-permission-rule__permission-icon iconoir-trash"
          :class="{ 'user-permission-rule__permission-icon--allowed': rule.effective_permissions.can_delete }"
        ></i>
        <span class="user-permission-rule__permission-label">
          {{ $t('userPermissions.permissions.delete') }}
        </span>
      </div>
    </div>

    <!-- Filters Info -->
    <div v-if="hasRowFilters || hasFieldPermissions" class="user-permission-rule__filters">
      <div v-if="hasRowFilters" class="user-permission-rule__filter-item">
        <i class="iconoir-filter-alt user-permission-rule__filter-icon"></i>
        <span class="user-permission-rule__filter-text">
          {{ $tc('userPermissions.filters.rowFilters', Object.keys(rule.row_filter).length) }}
        </span>
      </div>
      <div v-if="hasFieldPermissions" class="user-permission-rule__filter-item">
        <i class="iconoir-eye-off user-permission-rule__filter-icon"></i>
        <span class="user-permission-rule__filter-text">
          {{ $tc('userPermissions.filters.fieldPermissions', rule.field_permissions?.length || 0) }}
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div class="user-permission-rule__actions">
      <Button
        type="secondary"
        size="small"
        icon="iconoir-info-circle"
        @click="$emit('view-details', rule)"
      >
        {{ $t('userPermissions.actions.viewDetails') }}
      </Button>
      
      <Dropdown v-if="canManage" class="user-permission-rule__dropdown">
        <template #header>
          <Button
            type="secondary"
            size="small"
            icon="iconoir-more-horiz"
          >
            {{ $t('userPermissions.actions.more') }}
          </Button>
        </template>
        
        <DropdownItem
          icon="iconoir-edit"
          @click="$emit('update', rule)"
        >
          {{ $t('userPermissions.actions.edit') }}
        </DropdownItem>
        
        <DropdownItem
          icon="iconoir-refresh-double"
          @click="refreshFilteredView"
        >
          {{ $t('userPermissions.actions.refreshView') }}
        </DropdownItem>
        
        <DropdownItem
          v-if="rule.role !== 'admin'"
          icon="iconoir-trash"
          color="danger"
          @click="confirmDelete"
        >
          {{ $t('userPermissions.actions.revoke') }}
        </DropdownItem>
      </Dropdown>
    </div>

    <!-- Delete Confirmation Modal -->
    <ConfirmModal
      ref="deleteConfirmModal"
      :title="$t('userPermissions.deleteConfirm.title')"
      :content="deleteConfirmContent"
      confirm-button-type="danger"
      @confirm="$emit('delete', rule)"
    />
  </div>
</template>

<script>
import Avatar from '@baserow/modules/core/components/Avatar'
import Badge from '@baserow/modules/core/components/Badge'
import Button from '@baserow/modules/core/components/Button'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import ConfirmModal from '@baserow/modules/core/components/ConfirmModal'

export default {
  name: 'UserPermissionRule',
  components: {
    Avatar,
    Badge,
    Button,
    Dropdown,
    DropdownItem,
    ConfirmModal,
  },
  props: {
    rule: {
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
    canManage: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    userName() {
      return this.rule.user.first_name || 
             this.rule.user.username || 
             this.rule.user.email.split('@')[0]
    },
    userInitials() {
      if (this.rule.user.first_name) {
        const names = this.rule.user.first_name.split(' ')
        return names.map(name => name.charAt(0).toUpperCase()).join('')
      }
      return this.rule.user.email.charAt(0).toUpperCase()
    },
    hasRowFilters() {
      return this.rule.row_filter && Object.keys(this.rule.row_filter).length > 0
    },
    hasFieldPermissions() {
      return this.rule.field_permissions && this.rule.field_permissions.length > 0
    },
    deleteConfirmContent() {
      return this.$t('userPermissions.deleteConfirm.content', {
        userName: this.userName,
        tableName: this.table.name,
      })
    },
  },
  methods: {
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
    confirmDelete() {
      this.$refs.deleteConfirmModal.show()
    },
    async refreshFilteredView() {
      try {
        await this.$store.dispatch('userPermissions/refreshFilteredView', this.table.id)
        
        this.$store.dispatch('toast/success', {
          title: this.$t('userPermissions.success.viewRefreshed'),
          message: this.$t('userPermissions.success.viewRefreshedMessage', {
            userName: this.userName,
          }),
        })
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('userPermissions.errors.refreshViewFailed'),
          message: error.response?.data?.detail || error.message,
        })
      }
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@baserow/modules/core/assets/scss/colors';

.user-permission-rule {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid $color-neutral-200;
  border-radius: 8px;
  background: $color-neutral-50;
  margin-bottom: 12px;

  &:hover {
    background: $color-neutral-100;
    border-color: $color-neutral-300;
  }

  &__user {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 200px;
  }

  &__user-info {
    flex: 1;
  }

  &__user-name {
    margin: 0 0 2px;
    font-size: 14px;
    font-weight: 600;
    color: $color-neutral-900;
  }

  &__user-email {
    margin: 0;
    font-size: 12px;
    color: $color-neutral-600;
  }

  &__role {
    min-width: 100px;
  }

  &__permissions {
    display: flex;
    gap: 12px;
    flex: 1;
  }

  &__permission-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    min-width: 60px;
  }

  &__permission-icon {
    font-size: 16px;
    color: $color-neutral-400;
    transition: color 0.2s ease;

    &--allowed {
      color: $color-success-600;
    }
  }

  &__permission-label {
    font-size: 10px;
    color: $color-neutral-600;
    text-align: center;
  }

  &__filters {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 120px;
  }

  &__filter-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__filter-icon {
    font-size: 12px;
    color: $color-neutral-500;
  }

  &__filter-text {
    font-size: 11px;
    color: $color-neutral-600;
  }

  &__actions {
    display: flex;
    gap: 8px;
  }

  &__dropdown {
    .dropdown__item {
      &--danger {
        color: $color-error-600;

        &:hover {
          background-color: $color-error-50;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .user-permission-rule {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    &__user {
      min-width: unset;
      width: 100%;
    }

    &__permissions {
      justify-content: space-around;
      width: 100%;
    }

    &__filters {
      min-width: unset;
      width: 100%;
    }

    &__actions {
      width: 100%;
      justify-content: flex-end;
    }
  }
}
</style>