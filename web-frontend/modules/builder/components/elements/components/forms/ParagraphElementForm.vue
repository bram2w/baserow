<template>
  <form @submit.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('paragraphElementForm.textTitle') }}
      </label>
      <div class="control__elements">
        <textarea
          v-model="values.value"
          rows="12"
          :placeholder="$t('paragraphElementForm.textPlaceholder')"
          type="text"
          class="input paragraph-element-form__value"
        />
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'ParagraphElementForm',
  mixins: [form],
  props: {},
  data() {
    return {
      values: {
        value: '',
      },
    }
  },
}
</script>
