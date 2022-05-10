<template>
  <form class="context__form" @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('value')" class="control">
      <label class="control__label">{{
        $t('kanbanViewOptionForm.selectOption')
      }}</label>
      <div class="control__elements">
        <div class="select-options">
          <div class="select-options__item">
            <a
              ref="colorSelect"
              :class="
                'select-options__color' + ' background-color--' + values.color
              "
              @click="
                $refs.colorContext.toggle(
                  $refs.colorSelect,
                  'bottom',
                  'left',
                  4
                )
              "
            >
              <i class="fas fa-caret-down"></i>
            </a>
            <input
              v-model="values.value"
              class="input select-options__value"
              :class="{ 'input--error': fieldHasErrors('value') }"
              @blur="$v.values.value.$touch()"
            />
          </div>
        </div>
      </div>
      <div v-if="fieldHasErrors('value')" class="error">
        {{ $t('error.requiredField') }}
      </div>
    </FormElement>
    <slot></slot>
    <ColorSelectContext
      ref="colorContext"
      @selected="values.color = $event"
    ></ColorSelectContext>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import { randomColor } from '@baserow/modules/core/utils/colors'
import ColorSelectContext from '@baserow/modules/core/components/ColorSelectContext'

export default {
  name: 'KanbanViewOptionForm',
  components: { ColorSelectContext },
  mixins: [form],
  data() {
    return {
      allowedValues: ['color', 'value'],
      values: {
        color: randomColor(),
        value: '',
      },
    }
  },
  validations: {
    values: {
      value: { required },
    },
  },
}
</script>
