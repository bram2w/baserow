<template>
  <form @submit.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('headingElementForm.levelTitle') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.level" :show-search="false">
          <DropdownItem
            v-for="level in levels"
            :key="level.value"
            :name="level.name"
            :value="level.value"
          >
            {{ level.name }}
          </DropdownItem>
        </Dropdown>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('headingElementForm.textTitle') }}
      </label>
      <div class="control__elements">
        <input
          v-model="values.value"
          type="text"
          class="input"
          :placeholder="$t('headingElementForm.textPlaceholder')"
        />
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'HeaderElementForm',
  mixins: [form],
  props: {},
  data() {
    return {
      values: {
        value: '',
        level: 1,
      },
      levels: [...Array(6).keys()].map((level) => ({
        name: this.$t('headingElementForm.headingName', { level: level + 1 }),
        value: level + 1,
      })),
    }
  },
}
</script>
