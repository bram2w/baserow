<template>
  <form @submit.prevent @keydown.enter.prevent>
    <RadioGroup v-model="values.visibility" :options="options" vertical-layout>
    </RadioGroup>
  </form>
</template>

<script>
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'VisibilityForm',
  mixins: [elementForm],
  data() {
    return {
      values: {
        visibility: 'all',
      },
      allowedFields: ['visibility'],
      options: [
        { value: 'all', label: this.$t('visibilityForm.allVisitors') },
        {
          value: 'logged-in',
          label: this.$t('visibilityForm.loggedInVisitors'),
        },
        {
          value: 'not-logged',
          label: this.$t('visibilityForm.notLoggedInVisitors'),
        },
      ],
    }
  },
}
</script>
