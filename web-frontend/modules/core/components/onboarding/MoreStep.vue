<template>
  <div>
    <h1>{{ $t('moreStep.title') }}</h1>
    <FormInput
      v-model="role"
      :placeholder="$t('moreStep.roleOrJob') + '...'"
      :label="$t('moreStep.roleOrJob')"
      large
      :error="
        $v.role.$dirty && !$v.role.required ? $t('error.requiredField') : ''
      "
      @blur="$v.role.$touch()"
    />
    <FormGroup
      :label="$t('moreStep.people')"
      :error="
        $v.companySize.$dirty && !$v.companySize.required
          ? $t('error.requiredField')
          : ''
      "
    >
      <div class="flex flex-wrap" style="--gap: 8px">
        <Chips
          v-for="size in sizes"
          :key="size"
          :active="companySize === size"
          @click="selectSize(size)"
          >{{ size }}</Chips
        >
      </div>
    </FormGroup>
    <FormGroup
      :label="$t('moreStep.country')"
      :error="
        $v.country.$dirty && !$v.country.required
          ? $t('error.requiredField')
          : ''
      "
    >
      <Dropdown
        v-model="country"
        :class="{ 'dropdown--error': $v.country.$error }"
        @hide="$v.country.$touch()"
      >
        <DropdownItem
          v-for="countryName in countries"
          :key="countryName"
          :name="countryName"
          :value="countryName"
        ></DropdownItem>
      </Dropdown>
    </FormGroup>
    <FormGroup class="margin-top-3">
      <Checkbox v-model="share">{{ $t('moreStep.share') }}</Checkbox>
    </FormGroup>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import { countryList } from '@baserow/modules/core/utils/countries'

export default {
  name: 'MoreStep',
  data() {
    return {
      role: '',
      companySize: '',
      country: '',
      share: true,
    }
  },
  computed: {
    countries() {
      return countryList
    },
    sizes() {
      return ['0 - 10', '11 - 50', '51 - 200', '201 - 500', '500+']
    },
  },
  watch: {
    role() {
      this.updateValue()
    },
    country() {
      this.updateValue()
    },
    share() {
      this.updateValue()
    },
  },
  mounted() {
    this.updateValue()
  },
  methods: {
    isValid() {
      return !this.$v.$invalid
    },
    selectSize(size) {
      this.$v.companySize.$touch()
      this.companySize = size
      this.updateValue()
    },
    updateValue() {
      this.$emit('update-data', {
        role: this.role,
        companySize: this.companySize,
        country: this.country,
        share: this.share,
      })
    },
  },
  validations() {
    return {
      role: { required },
      companySize: { required },
      country: { required },
    }
  },
}
</script>
