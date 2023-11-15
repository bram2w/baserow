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
          class="input"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="fieldHasErrors('name')" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('workspace')" class="control">
      <label class="control__label">{{
        $t('apiTokenForm.workspaceLabel')
      }}</label>
      <Dropdown
        v-model="values.workspace"
        class="col-4"
        @hide="$v.values.workspace.$touch()"
      >
        <DropdownItem
          v-for="workspace in workspaces"
          :key="workspace.id"
          :name="workspace.name"
          :value="workspace.id"
        ></DropdownItem>
      </Dropdown>
      <div class="control__elements">
        <div v-if="fieldHasErrors('workspace')" class="error">
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
        workspace: '',
      },
    }
  },
  computed: {
    ...mapState({
      workspaces: (state) => state.workspace.items,
    }),
  },
  mounted() {
    this.$refs.name.focus()
  },
  validations: {
    values: {
      name: { required },
      workspace: { required },
    },
  },
}
</script>
