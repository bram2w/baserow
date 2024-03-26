<template>
  <form @submit.prevent @keydown.enter.prevent>
    <Radio v-model="values.visibility" value="all">
      {{ $t('visibilityForm.allVisitors') }}
    </Radio>
    <Radio v-model="values.visibility" value="logged-in">
      {{ $t('visibilityForm.loggedInVisitors') }}
    </Radio>
    <Radio v-model="values.visibility" value="not-logged">
      {{ $t('visibilityForm.notLoggedInVisitors') }}
    </Radio>
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
    }
  },
}
</script>
