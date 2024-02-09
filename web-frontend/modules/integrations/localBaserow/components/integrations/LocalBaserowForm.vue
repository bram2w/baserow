<template>
  <div>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('localBaserowForm.user') }}
      </label>
      <div class="local-baserow-form__user">
        <Presentation
          :title="values.authorized_user.first_name"
          :subtitle="values.authorized_user.username"
          :initials="values.authorized_user.first_name | nameAbbreviation"
          avatar-color="blue"
        />
        <div>{{ $t('localBaserowForm.userMessage') }}</div>
      </div>
    </FormElement>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  mixins: [form],
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      values: {
        authorized_user: {},
      },
      allowedValues: ['authorized_user'],
    }
  },
}
</script>
