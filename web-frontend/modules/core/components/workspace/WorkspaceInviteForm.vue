<template>
  <form @submit.prevent="submit">
    <h3>{{ $t('workspaceInviteForm.invitationFormTitle') }}</h3>
    <div class="row">
      <div class="col col-7">
        <FormElement :error="fieldHasErrors('email')" class="control">
          <div class="control__elements">
            <input
              ref="email"
              v-model="values.email"
              :class="{ 'input--error': fieldHasErrors('email') }"
              type="text"
              class="input input--small"
              @blur="$v.values.email.$touch()"
            />
            <div v-if="fieldHasErrors('email')" class="error">
              {{ $t('workspaceInviteForm.errorInvalidEmail') }}
            </div>
          </div>
        </FormElement>
      </div>
      <div class="col col-5">
        <FormElement class="control">
          <div class="control__elements">
            <div class="group-invite-form__role-selector">
              <slot name="roleSelectorLabel"></slot>
              <Dropdown
                v-model="values.permissions"
                class="group-invite-form__role-selector-dropdown"
                :show-search="false"
                :fixed-items="true"
                small
              >
                <DropdownItem
                  v-for="(role, index) in roles"
                  :key="index"
                  :ref="'role' + role.uid"
                  :name="role.name"
                  :value="role.uid"
                  :disabled="role.isDeactivated"
                  :description="role.description"
                  @click="clickOnDeactivatedItem($event)"
                >
                  {{ role.name }}
                  <Badge
                    v-if="role.showIsBillable && role.isBillable"
                    color="cyan"
                    size="small"
                    bold
                    >{{ $t('common.billable') }}
                  </Badge>
                  <Badge
                    v-else-if="
                      role.showIsBillable &&
                      !role.isBillable &&
                      atLeastOneBillableRole
                    "
                    color="yellow"
                    size="small"
                    bold
                    class="margin-left-1"
                    >{{ $t('common.free') }}
                  </Badge>
                  <i v-if="role.isDeactivated" class="iconoir-lock"></i>
                  <component
                    :is="deactivatedClickModal(role)"
                    :ref="'deactivatedClickModal-' + role.uid"
                    :v-if="deactivatedClickModal(role)"
                    :name="$t('workspaceInviteForm.additionalRoles')"
                    :workspace="workspace"
                  ></component>
                </DropdownItem>
              </Dropdown>
            </div>
          </div>
        </FormElement>
      </div>
      <div class="col col-12">
        <FormElement class="control">
          <div class="control__elements">
            <input
              ref="message"
              v-model="values.message"
              type="text"
              class="input input--small"
              :placeholder="
                $t('workspaceInviteForm.optionalMessagePlaceholder')
              "
            />
            <div v-if="fieldHasErrors('message')" class="error">
              {{
                $t('workspaceInviteForm.errorTooLongMessage', {
                  amount: messageMaxLength,
                })
              }}
            </div>
          </div>
        </FormElement>
      </div>
      <slot></slot>
    </div>
  </form>
</template>

<script>
import { required, email, maxLength } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

const MESSAGE_MAX_LENGTH = 250

export default {
  name: 'WorkspaceInviteForm',
  mixins: [form],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      values: {
        email: '',
        permissions: '',
        message: '',
      },
    }
  },
  computed: {
    messageMaxLength() {
      return MESSAGE_MAX_LENGTH
    },
    roles() {
      return this.workspace._.roles.filter((role) => role.isVisible)
    },
    defaultRole() {
      const activeRoles = this.roles.filter((role) => !role.isDeactivated)
      return activeRoles.length > 0 ? activeRoles[activeRoles.length - 1] : null
    },
    atLeastOneBillableRole() {
      return this.roles.some((role) => role.isBillable)
    },
  },
  watch: {
    defaultRole: {
      handler(role) {
        this.values.permissions = role.uid
      },
      immediate: true,
    },
  },
  methods: {
    deactivatedClickModal(role) {
      const allRoles = Object.values(this.$registry.getAll('roles'))
      return allRoles
        .find((r) => r.getUid() === role.uid)
        .getDeactivatedClickModal()
    },
    clickOnDeactivatedItem(value) {
      const role = this.roles.find((role) => role.uid === value)
      if (role && role.isDeactivated) {
        this.$refs[`deactivatedClickModal-${value}`][0].show()
      }
    },
  },
  validations: {
    values: {
      email: { required, email },
      message: { maxLength: maxLength(MESSAGE_MAX_LENGTH) },
    },
  },
}
</script>
