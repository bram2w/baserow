<template>
  <form @submit.prevent="submit">
    <h3>{{ $t('groupInviteForm.invitationFormTitle') }}</h3>
    <div class="row">
      <div class="col col-7">
        <FormElement :error="fieldHasErrors('email')" class="control">
          <div class="control__elements">
            <input
              ref="email"
              v-model="values.email"
              :class="{ 'input--error': fieldHasErrors('email') }"
              type="text"
              class="input"
              @blur="$v.values.email.$touch()"
            />
            <div v-if="fieldHasErrors('email')" class="error">
              {{ $t('groupInviteForm.errorInvalidEmail') }}
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
              >
                <DropdownItem
                  v-for="role in roles"
                  :key="role.uid"
                  :name="role.name"
                  :value="role.uid"
                  :description="role.description"
                >
                  {{ role.name }}
                  <Badge
                    v-if="!role.isBillable && atLeastOneBillableRole"
                    primary
                    class="margin-left-1"
                    >{{ $t('common.free') }}
                  </Badge>
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
              class="input"
              :placeholder="$t('groupInviteForm.optionalMessagePlaceholder')"
            />
            <div v-if="fieldHasErrors('message')" class="error">
              {{
                $t('groupInviteForm.errorTooLongMessage', {
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
  name: 'GroupInviteForm',
  mixins: [form],
  props: {
    group: {
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
      return this.group._.roles
    },
    defaultRole() {
      return this.roles.length > 0 ? this.roles[this.roles.length - 1] : null
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
  validations: {
    values: {
      email: { required, email },
      message: { maxLength: maxLength(MESSAGE_MAX_LENGTH) },
    },
  },
}
</script>
