<template>
  <Modal
    ref="modal"
    :title="$t('userPermissions.createRule.title')"
    @hidden="$emit('hidden')"
  >
    <form @submit.prevent="createRule">
      <!-- User Selection -->
      <FormGroup
        :label="$t('userPermissions.createRule.user')"
        required
        class="margin-bottom-2"
      >
        <Dropdown
          v-model="selectedUser"
          :placeholder="$t('userPermissions.createRule.selectUser')"
          :disabled="loading"
          class="user-permission-create__user-select"
        >
          <template #header>
            <div class="user-permission-create__user-header">
              <Avatar
                v-if="selectedUser"
                :initials="getUserInitials(selectedUser)"
                :name="getUserName(selectedUser)"
                size="small"
              />
              <span v-if="selectedUser" class="user-permission-create__user-name">
                {{ getUserName(selectedUser) }}
              </span>
              <span v-else class="user-permission-create__user-placeholder">
                {{ $t('userPermissions.createRule.selectUser') }}
              </span>
            </div>
          </template>
          
          <DropdownItem
            v-for="user in availableUsers"
            :key="user.id"
            @click="selectedUser = user"
          >
            <div class="user-permission-create__user-option">
              <Avatar
                :initials="getUserInitials(user)"
                :name="getUserName(user)"
                size="small"
              />
              <div class="user-permission-create__user-option-info">
                <div class="user-permission-create__user-option-name">
                  {{ getUserName(user) }}
                </div>
                <div class="user-permission-create__user-option-email">
                  {{ user.email }}
                </div>
              </div>
            </div>
          </DropdownItem>
        </Dropdown>
        <div v-if="errors.user" class="error">{{ errors.user }}</div>
      </FormGroup>

      <!-- Role Selection -->
      <FormGroup
        :label="$t('userPermissions.createRule.role')"
        required
        class="margin-bottom-2"
      >
        <div class="user-permission-create__roles">
          <div
            v-for="role in availableRoles"
            :key="role.value"
            class="user-permission-create__role"
            :class="{ 'user-permission-create__role--selected': selectedRole === role.value }"
            @click="selectedRole = role.value"
          >
            <div class="user-permission-create__role-header">
              <i :class="role.icon" class="user-permission-create__role-icon"></i>
              <h4 class="user-permission-create__role-title">{{ role.label }}</h4>
            </div>
            <p class="user-permission-create__role-description">{{ role.description }}</p>
            
            <!-- Permissions preview -->
            <div class="user-permission-create__role-permissions">
              <div
                v-for="permission in role.permissions"
                :key="permission.key"
                class="user-permission-create__role-permission"
                :class="{ 'user-permission-create__role-permission--allowed': permission.allowed }"
              >
                <i :class="permission.icon" class="user-permission-create__role-permission-icon"></i>
                <span class="user-permission-create__role-permission-label">{{ permission.label }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="errors.role" class="error">{{ errors.role }}</div>
      </FormGroup>

      <!-- Advanced Options Toggle -->
      <div class="user-permission-create__advanced-toggle margin-bottom-2">
        <a @click="showAdvanced = !showAdvanced">
          <i class="iconoir-nav-arrow-right" :class="{ 'iconoir-nav-arrow-down': showAdvanced }"></i>
          {{ $t('userPermissions.createRule.advancedOptions') }}
        </a>
      </div>

      <!-- Advanced Options -->
      <div v-if="showAdvanced" class="user-permission-create__advanced">
        <!-- Row Filters -->
        <FormGroup
          :label="$t('userPermissions.createRule.rowFilters')"
          :description="$t('userPermissions.createRule.rowFiltersDescription')"
          class="margin-bottom-2"
        >
          <div class="user-permission-create__row-filters">
            <div
              v-for="(filter, index) in rowFilters"
              :key="index"
              class="user-permission-create__row-filter"
            >
              <FormInput
                v-model="filter.field"
                :placeholder="$t('userPermissions.createRule.fieldName')"
                class="user-permission-create__row-filter-field"
              />
              <FormInput
                v-model="filter.value"
                :placeholder="$t('userPermissions.createRule.filterValue')"
                class="user-permission-create__row-filter-value"
              />
              <Button
                type="secondary"
                size="small"
                icon="iconoir-trash"
                @click="removeRowFilter(index)"
              />
            </div>
            <Button
              type="secondary"
              size="small"
              icon="iconoir-plus"
              @click="addRowFilter"
            >
              {{ $t('userPermissions.createRule.addFilter') }}
            </Button>
          </div>
          <div v-if="errors.rowFilters" class="error">{{ errors.rowFilters }}</div>
        </FormGroup>

        <!-- Field Permissions -->
        <FormGroup
          :label="$t('userPermissions.createRule.fieldPermissions')"
          :description="$t('userPermissions.createRule.fieldPermissionsDescription')"
          class="margin-bottom-2"
        >
          <div class="user-permission-create__field-permissions">
            <div
              v-for="field in fields"
              :key="field.id"
              class="user-permission-create__field-permission"
            >
              <div class="user-permission-create__field-info">
                <i :class="getFieldIcon(field)" class="user-permission-create__field-icon"></i>
                <span class="user-permission-create__field-name">{{ field.name }}</span>
              </div>
              <Dropdown
                v-model="fieldPermissions[field.id]"
                :placeholder="$t('userPermissions.createRule.defaultPermission')"
                class="user-permission-create__field-permission-select"
              >
                <DropdownItem
                  v-for="permission in fieldPermissionOptions"
                  :key="permission.value"
                  @click="fieldPermissions[field.id] = permission.value"
                >
                  <i :class="permission.icon" class="margin-right-1"></i>
                  {{ permission.label }}
                </DropdownItem>
              </Dropdown>
            </div>
          </div>
        </FormGroup>
      </div>

      <!-- Actions -->
      <div class="modal__actions">
        <Button
          type="secondary"
          @click="hide"
        >
          {{ $t('action.cancel') }}
        </Button>
        <Button
          type="primary"
          :loading="loading"
          :disabled="!canCreate"
        >
          {{ $t('userPermissions.createRule.create') }}
        </Button>
      </div>
    </form>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/components/Modal'
import Button from '@baserow/modules/core/components/Button'
import FormGroup from '@baserow/modules/core/components/FormGroup'
import FormInput from '@baserow/modules/core/components/FormInput'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import Avatar from '@baserow/modules/core/components/Avatar'

export default {
  name: 'CreateUserPermissionRuleModal',
  components: {
    Modal,
    Button,
    FormGroup,
    FormInput,
    Dropdown,
    DropdownItem,
    Avatar,
  },
  props: {
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    availableUsers: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      selectedUser: null,
      selectedRole: 'viewer',
      showAdvanced: false,
      rowFilters: [],
      fieldPermissions: {},
      errors: {},
    }
  },
  computed: {
    availableRoles() {
      return [
        {
          value: 'viewer',
          label: this.$t('userPermissions.roles.viewer'),
          description: this.$t('userPermissions.roleDescriptions.viewer'),
          icon: 'iconoir-user',
          permissions: [
            { key: 'read', label: this.$t('userPermissions.permissions.read'), icon: 'iconoir-eye', allowed: true },
            { key: 'create', label: this.$t('userPermissions.permissions.create'), icon: 'iconoir-plus', allowed: false },
            { key: 'update', label: this.$t('userPermissions.permissions.update'), icon: 'iconoir-edit', allowed: false },
            { key: 'delete', label: this.$t('userPermissions.permissions.delete'), icon: 'iconoir-trash', allowed: false },
          ]
        },
        {
          value: 'coordinator',
          label: this.$t('userPermissions.roles.coordinator'),
          description: this.$t('userPermissions.roleDescriptions.coordinator'),
          icon: 'iconoir-user-plus',
          permissions: [
            { key: 'read', label: this.$t('userPermissions.permissions.read'), icon: 'iconoir-eye', allowed: true },
            { key: 'create', label: this.$t('userPermissions.permissions.create'), icon: 'iconoir-plus', allowed: true },
            { key: 'update', label: this.$t('userPermissions.permissions.update'), icon: 'iconoir-edit', allowed: false },
            { key: 'delete', label: this.$t('userPermissions.permissions.delete'), icon: 'iconoir-trash', allowed: false },
          ]
        },
        {
          value: 'manager',
          label: this.$t('userPermissions.roles.manager'),
          description: this.$t('userPermissions.roleDescriptions.manager'),
          icon: 'iconoir-user-star',
          permissions: [
            { key: 'read', label: this.$t('userPermissions.permissions.read'), icon: 'iconoir-eye', allowed: true },
            { key: 'create', label: this.$t('userPermissions.permissions.create'), icon: 'iconoir-plus', allowed: true },
            { key: 'update', label: this.$t('userPermissions.permissions.update'), icon: 'iconoir-edit', allowed: true },
            { key: 'delete', label: this.$t('userPermissions.permissions.delete'), icon: 'iconoir-trash', allowed: false },
          ]
        },
      ]
    },
    fieldPermissionOptions() {
      return [
        {
          value: 'hidden',
          label: this.$t('userPermissions.fieldPermissions.hidden'),
          icon: 'iconoir-eye-off',
        },
        {
          value: 'read',
          label: this.$t('userPermissions.fieldPermissions.read'),
          icon: 'iconoir-eye',
        },
        {
          value: 'write',
          label: this.$t('userPermissions.fieldPermissions.write'),
          icon: 'iconoir-edit',
        },
      ]
    },
    canCreate() {
      return this.selectedUser && this.selectedRole && !this.loading
    },
    formData() {
      const data = {
        user_id: this.selectedUser?.id,
        role: this.selectedRole,
      }

      // Add row filters if any
      if (this.rowFilters.length > 0) {
        data.row_filter = {}
        this.rowFilters.forEach(filter => {
          if (filter.field && filter.value) {
            data.row_filter[filter.field] = filter.value
          }
        })
      }

      // Add field permissions if any
      const fieldPermissionsArray = []
      Object.entries(this.fieldPermissions).forEach(([fieldId, permission]) => {
        if (permission) {
          fieldPermissionsArray.push({
            field_id: parseInt(fieldId),
            permission: permission,
          })
        }
      })
      
      if (fieldPermissionsArray.length > 0) {
        data.field_permissions = fieldPermissionsArray
      }

      return data
    },
  },
  methods: {
    show() {
      this.$refs.modal.show()
    },
    hide() {
      this.$refs.modal.hide()
    },
    getUserName(user) {
      return user.first_name || user.username || user.email.split('@')[0]
    },
    getUserInitials(user) {
      if (user.first_name) {
        const names = user.first_name.split(' ')
        return names.map(name => name.charAt(0).toUpperCase()).join('')
      }
      return user.email.charAt(0).toUpperCase()
    },
    getFieldIcon(field) {
      // Return appropriate field type icon based on field type
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
    addRowFilter() {
      this.rowFilters.push({ field: '', value: '' })
    },
    removeRowFilter(index) {
      this.rowFilters.splice(index, 1)
    },
    validateForm() {
      this.errors = {}

      if (!this.selectedUser) {
        this.errors.user = this.$t('userPermissions.createRule.errors.userRequired')
      }

      if (!this.selectedRole) {
        this.errors.role = this.$t('userPermissions.createRule.errors.roleRequired')
      }

      // Validate row filters
      const invalidFilters = this.rowFilters.some(filter => 
        (filter.field && !filter.value) || (!filter.field && filter.value)
      )
      if (invalidFilters) {
        this.errors.rowFilters = this.$t('userPermissions.createRule.errors.incompleteFilters')
      }

      return Object.keys(this.errors).length === 0
    },
    async createRule() {
      if (!this.validateForm()) {
        return
      }

      this.loading = true
      
      try {
        const rule = await this.$store.dispatch('userPermissions/createRule', {
          tableId: this.table.id,
          values: this.formData,
        })

        this.$emit('created', rule)
        this.resetForm()
        this.hide()
      } catch (error) {
        // Handle validation errors from server
        if (error.response?.status === 400) {
          const data = error.response.data
          if (data.non_field_errors) {
            this.errors.general = data.non_field_errors[0]
          }
          Object.keys(data).forEach(key => {
            if (key !== 'non_field_errors') {
              this.errors[key] = Array.isArray(data[key]) ? data[key][0] : data[key]
            }
          })
        } else {
          this.$store.dispatch('toast/error', {
            title: this.$t('userPermissions.errors.createRuleFailed'),
            message: error.response?.data?.detail || error.message,
          })
        }
      } finally {
        this.loading = false
      }
    },
    resetForm() {
      this.selectedUser = null
      this.selectedRole = 'viewer'
      this.showAdvanced = false
      this.rowFilters = []
      this.fieldPermissions = {}
      this.errors = {}
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@baserow/modules/core/assets/scss/colors';

.create-user-permission-rule-modal {
.user-permission-create {
  &__user-select {
    width: 100%;
  }

  &__user-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    min-height: 40px;
  }

  &__user-name {
    font-weight: 500;
  }

  &__user-placeholder {
    color: $color-neutral-500;
  }

  &__user-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;

    &-info {
      flex: 1;
    }

    &-name {
      font-weight: 500;
      color: $color-neutral-900;
    }

    &-email {
      font-size: 12px;
      color: $color-neutral-600;
    }
  }

  &__roles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }

  &__role {
    padding: 16px;
    border: 2px solid $color-neutral-200;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      border-color: $color-primary-300;
    }

    &--selected {
      border-color: $color-primary-600;
      background-color: $color-primary-50;
    }

    &-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    &-icon {
      font-size: 18px;
      color: $color-primary-600;
    }

    &-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: $color-neutral-900;
    }

    &-description {
      margin: 0 0 16px;
      font-size: 14px;
      color: $color-neutral-600;
    }

    &-permissions {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }

    &-permission {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;

      &-icon {
        color: $color-neutral-400;
        font-size: 14px;
      }

      &-label {
        color: $color-neutral-600;
      }

      &--allowed {
        .user-permission-create__role-permission-icon {
          color: $color-success-600;
        }
        .user-permission-create__role-permission-label {
          color: $color-neutral-900;
          font-weight: 500;
        }
      }
    }
  }

  &__advanced-toggle {
    a {
      display: flex;
      align-items: center;
      gap: 8px;
      color: $color-primary-600;
      cursor: pointer;
      font-weight: 500;
      
      &:hover {
        color: $color-primary-700;
      }

      i {
        transition: transform 0.2s ease;
        font-size: 12px;
      }
    }
  }

  &__advanced {
    border-top: 1px solid $color-neutral-200;
    padding-top: 20px;
    margin-top: 20px;
  }

  &__row-filters {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__row-filter {
    display: flex;
    align-items: center;
    gap: 8px;

    &-field,
    &-value {
      flex: 1;
    }
  }

  &__field-permissions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 300px;
    overflow-y: auto;
  }

  &__field-permission {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border: 1px solid $color-neutral-200;
    border-radius: 6px;

    &-select {
      min-width: 150px;
    }
  }

  &__field-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
  }

  &__field-icon {
    color: $color-neutral-500;
  }

  &__field-name {
    font-weight: 500;
    color: $color-neutral-900;
  }
}
</style>