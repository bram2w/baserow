<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="login_button"
      :config-block-types="['button']"
      :theme="builder.theme"
    />
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
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'AuthFormElementForm',
  components: {
    CustomStyle,
  },
  mixins: [elementForm],
  inject: ['builder'],
  data() {
    return {
      allowedValues: ['user_source_id', 'styles'],
      values: {
        user_source_id: null,
        styles: {},
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
