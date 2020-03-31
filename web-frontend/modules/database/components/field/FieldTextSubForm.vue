<template>
  <div>
    <div class="control">
      <div class="control-elements">
        <input
          ref="text_default"
          v-model="values.text_default"
          type="text"
          class="input"
          placeholder="Default text"
        />
      </div>
    </div>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'FieldTextSubForm',
  mixins: [form],
  data() {
    return {
      allowedValues: ['text_default'],
      values: {
        text_default: '',
      },
    }
  },
  methods: {
    isFormValid() {
      return true
    },
  },
}
</script>
