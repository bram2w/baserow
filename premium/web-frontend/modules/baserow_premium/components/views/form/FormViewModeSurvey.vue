<template>
  <div class="form-view-survey">
    <template v-if="!submitted">
      <form @submit.prevent="validateAndNext(questionIndex)">
        <div
          v-for="(field, index) in visibleFields"
          :key="field.field.id"
          class="form-view-survey__center"
          :class="{
            'form-view-survey__center--before': index < questionIndex,
            'form-view-survey__center--after': index > questionIndex,
          }"
        >
          <div class="form-view-survey__center-inner-1">
            <div class="form-view-survey__center-inner-2">
              <FormPageField
                :ref="'field-' + field.field.id"
                :value="values['field_' + field.field.id]"
                :slug="$route.params.slug"
                :field="field"
                @input="updateValue('field_' + field.field.id, $event)"
                @focussed="questionIndex = index"
              ></FormPageField>
              <div class="form-view__field-actions">
                <a
                  v-if="index < visibleFields.length - 1"
                  class="button button--primary button--large"
                  @click="validateAndNext(index)"
                  >Next</a
                >
                <button
                  v-else-if="index >= visibleFields.length - 1"
                  class="button button--primary button--large"
                  :class="{ 'button--loading': loading }"
                  :disabled="loading"
                >
                  {{ submitText }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </form>
      <div
        class="form-view-survey__footer"
        :class="{ 'form-view-survey__footer--single': !showLogo }"
      >
        <FormViewPoweredBy v-if="showLogo"></FormViewPoweredBy>
        <div class="form-view-survey__pagination">
          <div class="form-view-survey__pagination-buttons">
            <a
              class="form-view-survey__pagination-button"
              :class="{
                'form-view-survey__pagination-button--disabled': !canPrevious,
              }"
              @click="previous"
            >
              <i class="fas fa-chevron-up"></i>
            </a>
            <a
              class="form-view-survey__pagination-button"
              :class="{
                'form-view-survey__pagination-button--disabled': !canNext,
              }"
              @click="next"
            >
              <i class="fas fa-chevron-down"></i>
            </a>
          </div>
        </div>
      </div>
    </template>
    <div v-else-if="submitted" class="form-view-survey__center">
      <div class="form-view-survey__center-inner">
        <FormViewSubmitted
          :is-redirect="isRedirect"
          :submit-action-redirect-url="submitActionRedirectUrl"
          :submit-action-message="submitActionMessage"
        ></FormViewSubmitted>
      </div>
    </div>
  </div>
</template>

<script>
import baseFormViewMode from '@baserow/modules/database/mixins/baseFormViewMode'
import FormPageField from '@baserow/modules/database/components/view/form/FormPageField'
import FormViewPoweredBy from '@baserow/modules/database/components/view/form/FormViewPoweredBy'
import FormViewSubmitted from '@baserow/modules/database/components/view/form/FormViewSubmitted'

export default {
  name: 'FormViewModeSurvey',
  components: {
    FormPageField,
    FormViewPoweredBy,
    FormViewSubmitted,
  },
  mixins: [baseFormViewMode],
  data() {
    return {
      questionIndex: 0,
    }
  },
  computed: {
    canPrevious() {
      return this.questionIndex > 0
    },
    canNext() {
      return this.questionIndex < this.visibleFields.length - 1
    },
  },
  methods: {
    previous() {
      if (!this.canPrevious) {
        return
      }

      this.questionIndex--
    },
    next() {
      if (!this.canNext) {
        return
      }

      this.questionIndex++
    },
    validateAndNext(fieldIndex) {
      const field = this.visibleFields[fieldIndex]
      field._.touched = true

      const ref = this.$refs['field-' + field.field.id][0]

      if (!ref.isValid()) {
        return
      }

      if (fieldIndex === this.visibleFields.length - 1) {
        this.$emit('submit')
      } else {
        this.next()
      }
    },
  },
}
</script>
