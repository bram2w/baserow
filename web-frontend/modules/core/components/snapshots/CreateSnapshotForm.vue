<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">
        {{ $t('snapshotsModal.createLabel') }}
      </label>
      <div class="control__elements">
        <div class="modal-progress__actions">
          <slot name="input">
            <input
              ref="name"
              v-model="values.name"
              :class="{ 'input--error': fieldHasErrors('name') }"
              type="text"
              class="input snapshots-modal__name-input"
              @blur="$v.values.name.$touch()"
            />
          </slot>
          <slot></slot>
        </div>
      </div>
    </FormElement>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import moment from '@baserow/modules/core/moment'

export default {
  name: 'CreateSnapshotForm',
  mixins: [form],
  props: {
    snapshots: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      values: {
        name: this.getDefaultName(),
      },
    }
  },
  methods: {
    getDefaultName() {
      const datetime = moment().utc().format('YYYY-MM-DD HH:mm')
      return `${this.$t('snapshotsModal.snapshot')} ${datetime} UTC`
    },
    resetName() {
      this.values.name = this.getDefaultName()
    },
    mustHaveUniqueName(param) {
      const names = this.snapshots.map((snapshot) => snapshot.name)
      return !names.includes(param)
    },
  },
  validations() {
    return {
      values: {
        name: {
          required,
          mustHaveUniqueName: this.mustHaveUniqueName,
        },
      },
    }
  },
}
</script>
