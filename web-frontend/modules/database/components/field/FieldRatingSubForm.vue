<template>
  <div class="rating-field-form">
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldRatingSubForm.color')
      }}</label>
      <div class="control__elements">
        <a
          :ref="'color-select'"
          :class="'rating-field__color' + ' background-color--' + values.color"
          @click="openColor()"
        >
          <i class="fas fa-caret-down"></i>
        </a>
      </div>
    </div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldRatingSubForm.style')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.style"
          class="dropdown--floating rating-field-form__dropdown-style"
          :class="{ 'dropdown--error': $v.values.style.$error }"
          :show-search="false"
          @hide="$v.values.style.$touch()"
        >
          <DropdownItem
            v-for="style in styles"
            :key="style"
            name=""
            :value="style"
            :icon="style"
          />
        </Dropdown>
      </div>
    </div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldRatingSubForm.maxValue')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.max_value"
          class="dropdown--floating"
          :class="{ 'dropdown--error': $v.values.max_value.$error }"
          :show-search="false"
          @hide="$v.values.max_value.$touch()"
        >
          <DropdownItem
            v-for="index in 10"
            :key="index"
            :name="`${index}`"
            :value="index"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <ColorSelectContext
      ref="colorContext"
      :colors="colors"
      @selected="updateColor($event)"
    ></ColorSelectContext>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import ColorSelectContext from '@baserow/modules/core/components/ColorSelectContext'

const colors = [['dark-blue', 'dark-green', 'dark-orange', 'dark-red']]

export default {
  name: 'FieldRatingSubForm',
  components: { ColorSelectContext },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['max_value', 'color', 'style'],
      values: {
        max_value: 5,
        color: 'dark-orange',
        style: 'star',
      },
      colors,
      styles: ['star', 'heart', 'thumbs-up', 'flag', 'smile'],
    }
  },
  methods: {
    openColor() {
      this.$refs.colorContext.setActive(this.values.color)
      this.$refs.colorContext.toggle(
        this.$refs['color-select'],
        'bottom',
        'left',
        4
      )
    },
    updateColor(color) {
      this.values.color = color
    },
  },
  validations: {
    values: {
      max_value: { required },
      color: { required },
      style: { required },
    },
  },
}
</script>
