<template>
  <Modal
    ref="modal"
    :title="$t('userPermissions.editRule.title')"
    @hidden="$emit('hidden')"
  >
    <form v-if="rule" @submit.prevent="updateRule">
      <!-- User Info (Read-only) -->
      <FormGroup
        :label="$t('userPermissions.editRule.user')"
        class="margin-bottom-2"
      >
        <div class="user-permission-edit__user-display">
          <Avatar
            :initials="userInitials"
            :name="userName"
            size="small"
          />
          <div class="user-permission-edit__user-info">
            <div class="user-permission-edit__user-name">{{ userName }}</div>
            <div class="user-permission-edit__user-email">{{ rule.user.email }}</div>
          </div>
        </div>
      </FormGroup>

      <!-- Role Selection -->
      <FormGroup
        :label="$t('userPermissions.editRule.role')"
        required
        class="margin-bottom-2"
      >
        <div class="user-permission-edit__roles">
          <div
            v-for="roleOption in availableRoles"
            :key="roleOption.value"
            class="user-permission-edit__role"
            :class="{ 'user-permission-edit__role--selected': formData.role === roleOption.value }"
            @click="formData.role = roleOption.value"
          >
            <div class="user-permission-edit__role-header">
              <i :class="roleOption.icon" class="user-permission-edit__role-icon"></i>
              <h4 class="user-permission-edit__role-title">{{ roleOption.label }}</h4>
            </div>
            <p class="user-permission-edit__role-description">{{ roleOption.description }}</p>
          </div>
        </div>
        <div v-if="errors.role" class="error">{{ errors.role }}</div>
      </FormGroup>

      <!-- Advanced Options -->
      <div class="user-permission-edit__advanced-toggle margin-bottom-2">
        <a @click="showAdvanced = !showAdvanced">
          <i class="iconoir-nav-arrow-right" :class="{ 'iconoir-nav-arrow-down': showAdvanced }"></i>
          {{ $t('userPermissions.editRule.advancedOptions') }}
        </a>
      </div>

      <div v-if="showAdvanced" class="user-permission-edit__advanced">
        <!-- Row Filters -->
        <FormGroup
          :label="$t('userPermissions.editRule.rowFilters')"
          :description="$t('userPermissions.editRule.rowFiltersDescription')"
          class="margin-bottom-2"
        >
          <div class="user-permission-edit__row-filters">
            <div
              v-for="(filter, index) in rowFilters"
              :key="index"
              class="user-permission-edit__row-filter"
            >
              <FormInput
                v-model="filter.field"
                :placeholder="$t('userPermissions.editRule.fieldName')"
                class="user-permission-edit__row-filter-field"
              />
              <FormInput
                v-model="filter.value"
                :placeholder="$t('userPermissions.editRule.filterValue')"
                class="user-permission-edit__row-filter-value"
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
              {{ $t('userPermissions.editRule.addFilter') }}
            </Button>
          </div>
        </FormGroup>

        <!-- Field Permissions -->
        <FormGroup
          :label="$t('userPermissions.editRule.fieldPermissions')"
          :description="$t('userPermissions.editRule.fieldPermissionsDescription')"
          class="margin-bottom-2"
        >
          <div class="user-permission-edit__field-permissions">
            <div
              v-for="field in fields"
              :key="field.id"
              class="user-permission-edit__field-permission"
            >
              <div class="user-permission-edit__field-info">
                <i :class="getFieldIcon(field)" class="user-permission-edit__field-icon"></i>
                <span class="user-permission-edit__field-name">{{ field.name }}</span>
              </div>
              <Dropdown
                v-model="fieldPermissions[field.id]"
                :placeholder="$t('userPermissions.editRule.defaultPermission')"
                class="user-permission-edit__field-permission-select"
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
          :disabled="!hasChanges"
        >
          {{ $t('userPermissions.editRule.update') }}
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
  name: 'EditUserPermissionRuleModal',
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
  data() {
    return {
      loading: false,
      showAdvanced: false,
      formData: {},
      rowFilters: [],
      fieldPermissions: {},
      errors: {},
    }
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
    availableRoles() {
      return [
        {
          value: 'viewer',
          label: this.$t('userPermissions.roles.viewer'),
          description: this.$t('userPermissions.roleDescriptions.viewer'),
          icon: 'iconoir-user',
        },
        {
          value: 'coordinator',
          label: this.$t('userPermissions.roles.coordinator'),
          description: this.$t('userPermissions.roleDescriptions.coordinator'),
          icon: 'iconoir-user-plus',
        },
        {
          value: 'manager',
          label: this.$t('userPermissions.roles.manager'),
          description: this.$t('userPermissions.roleDescriptions.manager'),
          icon: 'iconoir-user-star',
        },
      ]
    },
    fieldPermissionOptions() {
      return [
        {
          value: null,
          label: this.$t('userPermissions.fieldPermissions.default'),
          icon: 'iconoir-circle',
        },
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
    hasChanges() {
      if (!this.rule) return false
      
      // Check role change
      if (this.formData.role !== this.rule.role) return true
      
      // Check row filters change
      const originalFilters = this.rule.row_filter || {}
      const currentFilters = {}
      this.rowFilters.forEach(filter => {
        if (filter.field && filter.value) {
          currentFilters[filter.field] = filter.value
        }
      })
      
      if (JSON.stringify(originalFilters) !== JSON.stringify(currentFilters)) return true
      
      // Check field permissions change
      const originalFieldPerms = {}
      if (this.rule.field_permissions) {
        this.rule.field_permissions.forEach(fp => {
          originalFieldPerms[fp.field.id] = fp.permission
        })
      }
      
      return JSON.stringify(originalFieldPerms) !== JSON.stringify(this.fieldPermissions)
    },
  },
  watch: {
    rule: {
      immediate: true,
      handler(newRule) {
        if (newRule) {
          this.initializeForm()
        }
      },
    },
  },
  methods: {
    show() {
      this.$refs.modal.show()
    },
    hide() {
      this.$refs.modal.hide()
    },
    initializeForm() {
      if (!this.rule) return
      
      this.formData = {
        role: this.rule.role,
      }
      
      // Initialize row filters
      this.rowFilters = []
      if (this.rule.row_filter) {
        Object.entries(this.rule.row_filter).forEach(([field, value]) => {
          this.rowFilters.push({ field, value })
        })
      }
      
      // Initialize field permissions
      this.fieldPermissions = {}
      if (this.rule.field_permissions) {
        this.rule.field_permissions.forEach(fp => {
          this.fieldPermissions[fp.field.id] = fp.permission
        })
      }
      
      this.errors = {}
      this.showAdvanced = this.rowFilters.length > 0 || Object.keys(this.fieldPermissions).length > 0
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
    addRowFilter() {
      this.rowFilters.push({ field: '', value: '' })
    },
    removeRowFilter(index) {
      this.rowFilters.splice(index, 1)
    },
    async updateRule() {
      if (!this.validateForm()) {
        return
      }

      const updateData = {
        role: this.formData.role,
      }

      // Add row filters if any
      if (this.rowFilters.length > 0) {
        updateData.row_filter = {}
        this.rowFilters.forEach(filter => {
          if (filter.field && filter.value) {
            updateData.row_filter[filter.field] = filter.value
          }
        })
      } else {
        updateData.row_filter = {}
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
      updateData.field_permissions = fieldPermissionsArray

      this.loading = true
      
      try {
        const updatedRule = await this.$store.dispatch('userPermissions/updateRule', {
          tableId: this.table.id,
          userId: this.rule.user.id,
          values: updateData,
        })

        this.$emit('updated', updatedRule)
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
            title: this.$t('userPermissions.errors.updateRuleFailed'),
            message: error.response?.data?.detail || error.message,
          })
        }
      } finally {
        this.loading = false
      }
    },
    validateForm() {
      this.errors = {}

      if (!this.formData.role) {
        this.errors.role = this.$t('userPermissions.editRule.errors.roleRequired')
      }

      // Validate row filters
      const invalidFilters = this.rowFilters.some(filter => 
        (filter.field && !filter.value) || (!filter.field && filter.value)
      )
      if (invalidFilters) {
        this.errors.rowFilters = this.$t('userPermissions.editRule.errors.incompleteFilters')
      }

      return Object.keys(this.errors).length === 0
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@baserow/modules/core/assets/scss/colors';

.edit-user-permission-rule-modal {
.user-permission-edit {
  &__user-display {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border: 1px solid $color-neutral-200;
    border-radius: 6px;
    background: $color-neutral-50;
  }

  &__user-info {
    flex: 1;
  }

  &__user-name {
    font-weight: 600;
    color: $color-neutral-900;
  }

  &__user-email {
    font-size: 12px;
    color: $color-neutral-600;
  }

  &__roles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
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
      font-size: 16px;
      color: $color-primary-600;
    }

    &-title {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: $color-neutral-900;
    }

    &-description {
      margin: 0;
      font-size: 12px;
      color: $color-neutral-600;
      line-height: 1.4;
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
    gap: 8px;
    max-height: 250px;
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
      min-width: 140px;
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