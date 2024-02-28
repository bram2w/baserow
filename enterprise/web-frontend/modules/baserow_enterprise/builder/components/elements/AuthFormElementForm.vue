<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup :label="$t('authFormElementForm.userSource')">
      <Dropdown v-model="values.user_source_id" :show-search="false">
        <DropdownItem
          v-for="userSource in userSources"
          :key="userSource.id"
          :name="userSource.name"
          :value="userSource.id"
        />
      </Dropdown>
    </FormGroup>
  </form>
</template>

<script>
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'AuthFormElementForm',
  mixins: [elementForm],
  inject: ['builder'],
  data() {
    return {
      allowedValues: ['user_source_id'],
      values: {
        user_source_id: null,
      },
    }
  },
  computed: {
    userSources() {
      return this.$store.getters['userSource/getUserSources'](this.builder)
    },
  },
  methods: {},
  validations() {
    return {}
  },
}
</script>
