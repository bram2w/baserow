<template>
  <div class="control__elements">
    <div v-if="!editing">
      <span class="field-password__dots">{{ value ? '••••••••••' : '' }}</span>
      <a @click="change()">
        {{
          value ? $t('action.change') : $t('rowEditFieldPassword.setPassword')
        }}
      </a>
    </div>
    <div v-else>
      <FormGroup required :error="touched && !valid">
        <div class="flex align-items-center">
          <FormInput
            ref="input"
            v-model="copy"
            type="password"
            :error="touched && !valid"
            :disabled="readOnly"
            class="col-6"
            @keyup.enter="unselect()"
          />
          <a @click="unselect()">{{ $t('action.save') }}</a>
          <a class="color-error" @click="editing = false">{{
            $t('action.cancel')
          }}</a>
        </div>

        <template #error>
          {{ error }}
        </template>
      </FormGroup>
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'

export default {
  name: 'RowEditFieldPassword',
  mixins: [rowEditField, rowEditFieldInput],
  methods: {
    change() {
      this.editing = true
      this.copy = ''
      this.$nextTick(() => {
        this.$refs.input.focus()
      })
    },
    cancel() {
      this.editing = false
      this.copy = ''
    },
  },
}
</script>
