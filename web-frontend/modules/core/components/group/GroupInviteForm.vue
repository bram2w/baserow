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
            <Dropdown v-model="values.permissions" :show-search="false">
              <DropdownItem
                v-for="role in roles"
                :key="role.value"
                :name="role.name"
                :value="role.value"
                :description="role.description"
              ></DropdownItem>
            </Dropdown>
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
          </div>
        </FormElement>
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
  computed: {
    roles() {
      return this.$store.getters['roles/getAllRoles'].map(
        ({ value, name, description }) => ({
          value,
          name: this.$t(name),
          description: this.$t(description),
        })
      )
    },
  },
  validations: {
    values: {
      email: { required, email },
    },
  },
}
</script>
