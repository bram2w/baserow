<template>
  <form @submit.prevent="submit">
    <h3>Invite by email</h3>
    <div class="row">
      <div class="col col-7">
        <div class="control">
          <div class="control__elements">
            <input
              ref="email"
              v-model="values.email"
              :class="{ 'input--error': $v.values.email.$error }"
              type="text"
              class="input"
              @blur="$v.values.email.$touch()"
            />
            <div v-if="$v.values.email.$error" class="error">
              Please enter a valid e-mail address.
            </div>
          </div>
        </div>
      </div>
      <div class="col col-5">
        <div class="control">
          <div class="control__elements">
            <Dropdown v-model="values.permissions" :show-search="false">
              <DropdownItem
                name="Admin"
                value="ADMIN"
                description="Can fully configure and edit groups and applications."
              ></DropdownItem>
              <DropdownItem
                name="Member"
                value="MEMBER"
                description="Can fully configure and edit applications."
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-12">
        <div class="control">
          <div class="control__elements">
            <input
              ref="message"
              v-model="values.message"
              type="text"
              class="input"
              placeholder="Optional message"
            />
          </div>
        </div>
      </div>
      <slot></slot>
    </div>
  </form>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'GroupInviteForm',
  mixins: [form],
  data() {
    return {
      loading: false,
      values: {
        email: '',
        permissions: 'MEMBER',
        message: '',
      },
    }
  },
  validations: {
    values: {
      email: { required, email },
    },
  },
}
</script>
