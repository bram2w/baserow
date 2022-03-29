<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">{{ $t('apiTokenForm.nameLabel') }}</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input input--large"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="fieldHasErrors('name')" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('group')" class="control">
      <label class="control__label">{{ $t('apiTokenForm.groupLabel') }}</label>
      <Dropdown
        v-model="values.group"
        class="col-4"
        @hide="$v.values.group.$touch()"
      >
        <DropdownItem
          v-for="group in groups"
          :key="group.id"
          :name="group.name"
          :value="group.id"
        ></DropdownItem>
      </Dropdown>
      <div class="control__elements">
        <div v-if="fieldHasErrors('group')" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <slot></slot>
  </form>
</template>

<script>
import { mapState } from 'vuex'
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'APITokenForm',
  mixins: [form],
  data() {
    return {
      values: {
        name: '',
        group: '',
      },
    }
  },
  computed: {
    ...mapState({
      groups: (state) => state.group.items,
    }),
  },
  mounted() {
    this.$refs.name.focus()
  },
  validations: {
    values: {
      name: { required },
      group: { required },
    },
  },
}
</script>
