<template>
  <form @submit.prevent="submit" @input="$emit('formchange')">
    <div v-if="!isDeprecated">
      <Alert
        v-if="!values.active"
        simple
        type="primary"
        icon="exclamation"
        :title="$t('webhookForm.deactivated.title')"
      >
        {{ $t('webhookForm.deactivated.content') }}
        <p>
          <a
            class="button button--ghost margin-top-1"
            @click="values.active = true"
            >{{ $t('webhookForm.deactivated.activate') }}</a
          >
        </p>
      </Alert>
      <div class="row">
        <div class="col col-12">
          <FormElement :error="fieldHasErrors('name')" class="control">
            <label class="control__label">
              {{ $t('webhookForm.inputLabels.name') }}
            </label>
            <div class="control__elements">
              <input
                v-model="values.name"
                class="input"
                :class="{ 'input--error': fieldHasErrors('name') }"
                @blur="$v.values.name.$touch()"
              />
              <div v-if="fieldHasErrors('name')" class="error">
                {{ $t('error.requiredField') }}
              </div>
            </div>
          </FormElement>
        </div>
        <div class="col col-12">
          <div class="control">
            <label class="control__label">
              {{ $t('webhookForm.inputLabels.userFieldNames') }}
            </label>
            <div class="control__elements">
              <Checkbox v-model="values.use_user_field_names">{{
                $t('webhookForm.checkbox.sendUserFieldNames')
              }}</Checkbox>
            </div>
          </div>
        </div>
        <div class="col col-4">
          <div class="control">
            <div class="control__label">
              {{ $t('webhookForm.inputLabels.requestMethod') }}
            </div>
            <div class="control__elements">
              <Dropdown v-model="values.request_method">
                <DropdownItem name="GET" value="GET"></DropdownItem>
                <DropdownItem name="POST" value="POST"></DropdownItem>
                <DropdownItem name="PATCH" value="PATCH"></DropdownItem>
                <DropdownItem name="PUT" value="PUT"></DropdownItem>
                <DropdownItem name="DELETE" value="DELETE"></DropdownItem>
              </Dropdown>
            </div>
          </div>
        </div>
        <div class="col col-8">
          <FormElement :error="fieldHasErrors('url')" class="control">
            <label class="control__label">
              {{ $t('webhookForm.inputLabels.url') }}
            </label>
            <div class="control__elements">
              <input
                v-model="values.url"
                :placeholder="$t('webhookForm.inputLabels.url')"
                class="input"
                :class="{ 'input--error': fieldHasErrors('url') }"
                @blur="$v.values.url.$touch()"
              />
              <div
                v-if="
                  fieldHasErrors('url') &&
                  (!$v.values.url.required || !$v.values.url.url)
                "
                class="error"
              >
                {{ $t('webhookForm.errors.urlField') }}
              </div>
              <div
                v-else-if="$v.values.url.$error && !$v.values.url.maxLength"
                class="error"
              >
                {{
                  $t('error.maxLength', {
                    max: $v.values.url.$params.maxLength.max,
                  })
                }}
              </div>
            </div>
          </FormElement>
        </div>
      </div>
      <div class="control">
        <label class="control__label">
          {{ $t('webhookForm.inputLabels.events') }}
        </label>
        <div class="control__elements">
          <Radio v-model="values.include_all_events" :value="true">{{
            $t('webhookForm.radio.allEvents')
          }}</Radio>
          <Radio v-model="values.include_all_events" :value="false">
            {{ $t('webhookForm.radio.customEvents') }}
          </Radio>
          <div v-if="!values.include_all_events" class="webhook__types">
            <Checkbox
              v-for="webhookEvent in webhookEventTypes"
              :key="webhookEvent.type"
              :value="values.events.includes(webhookEvent.type)"
              class="webhook__type"
              @input="
                $event
                  ? values.events.push(webhookEvent.type)
                  : values.events.splice(
                      values.events.indexOf(webhookEvent.type),
                      1
                    )
              "
              >{{ webhookEvent.getName() }}</Checkbox
            >
          </div>
        </div>
      </div>
      <div class="control">
        <div class="control__label">
          {{ $t('webhookForm.inputLabels.headers') }}
        </div>
        <div class="control__elements">
          <div
            v-for="(header, index) in headers.concat({
              name: '',
              value: '',
            })"
            :key="`header-input-${index}`"
            class="webhook__header"
          >
            <div class="webhook__header-row">
              <input
                v-model="header.name"
                class="input webhook__header-key"
                :class="{
                  'input--error':
                    !lastHeader(index) && $v.headers.$each[index].name.$error,
                }"
                :placeholder="$t('webhookForm.inputLabels.name')"
                @input="
                  lastHeader(index) && addHeader(header.name, header.value)
                "
                @blur="
                  !lastHeader(index) && $v.headers.$each[index].name.$touch()
                "
              />
              <input
                v-model="header.value"
                class="input webhook__header-value"
                :class="{
                  'input--error':
                    !lastHeader(index) && $v.headers.$each[index].value.$error,
                }"
                :placeholder="$t('webhookForm.inputLabels.value')"
                @input="
                  lastHeader(index) && addHeader(header.name, header.value)
                "
                @blur="
                  !lastHeader(index) && $v.headers.$each[index].value.$touch()
                "
              />
              <a
                v-if="!lastHeader(index)"
                class="button button--error webhook__header-delete"
                @click="removeHeader(index)"
              >
                <i class="fas fa-trash button__icon"></i>
              </a>
            </div>
          </div>
          <div v-if="$v.headers.$anyError" class="error">
            {{ $t('webhookForm.errors.invalidHeaders') }}
          </div>
        </div>
      </div>
      <div class="control">
        <div class="control__label">
          {{ $t('webhookForm.inputLabels.example') }}
        </div>
        <div class="control__elements">
          <div class="webhook__code-with-dropdown">
            <div class="webhook__code-dropdown">
              <Dropdown
                v-model="exampleWebhookEventType"
                class="dropdown--floating-left"
              >
                <DropdownItem
                  v-for="webhookEvent in webhookEventTypes"
                  :key="webhookEvent.type"
                  :name="webhookEvent.getName()"
                  :value="webhookEvent.type"
                ></DropdownItem>
              </Dropdown>
            </div>
            <div class="webhook__code-container">
              <pre
                class="webhook__code"
              ><code>{{ JSON.stringify(testExample, null, 4)}}</code></pre>
            </div>
          </div>
        </div>
      </div>
      <a class="button button--ghost" @click="openTestModal()">{{
        $t('webhookForm.triggerButton')
      }}</a>
      <slot></slot>
      <TestWebhookModal ref="testModal" />
    </div>
    <div v-else>
      <div class="alert alert--error alert--has-icon">
        <div class="alert__icon">
          <i class="fas fa-exclamation"></i>
        </div>
        <div class="alert__title">
          {{ $t('webhookForm.deprecatedEventType.title') }}
        </div>
        <p class="alert__content">
          {{ $t('webhookForm.deprecatedEventType.description') }}
          <button
            class="button webhook__convert"
            @click="convertFromDeprecated"
          >
            {{ $t('webhookForm.deprecatedEventType.convert') }}
          </button>
        </p>
      </div>
    </div>
  </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { required, maxLength, url } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import error from '@baserow/modules/core/mixins/error'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import Radio from '@baserow/modules/core/components/Radio'
import TestWebhookModal from '@baserow/modules/database/components/webhook/TestWebhookModal'

export default {
  name: 'WebhookForm',
  components: {
    Checkbox,
    Radio,
    TestWebhookModal,
  },
  mixins: [form, error],
  props: {
    table: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: [
        'name',
        'url',
        'request_method',
        'include_all_events',
        'use_user_field_names',
        'headers',
        'events',
        'active',
      ],
      values: {
        name: '',
        active: true,
        use_user_field_names: true,
        url: '',
        request_method: 'POST',
        include_all_events: true,
        events: [],
      },
      headers: [],
      exampleWebhookEventType: '',
    }
  },
  computed: {
    webhookEventTypes() {
      return this.$registry.getAll('webhookEvent')
    },
    isDeprecated() {
      return this.values.events.some((eventName) =>
        ['row.created', 'row.updated', 'row.deleted'].includes(eventName)
      )
    },
    /**
     * Generates an example payload of the webhook event based on the chosen webhook
     * event type.
     */
    testExample() {
      if (this.exampleWebhookEventType === '') {
        return {}
      }

      const rowExample = {
        id: 0,
        order: '1.00000000000000000000',
      }
      this.fields.forEach((field) => {
        const fieldType = this.$registry.get('field', field.type)
        const empty = fieldType.getEmptyValue(field)
        rowExample[
          this.values.use_user_field_names ? field.name : `field_${field.id}`
        ] = empty
      })
      const webhookEvent = this.$registry.get(
        'webhookEvent',
        this.exampleWebhookEventType
      )
      return webhookEvent.getExamplePayload(this.table, rowExample)
    },
    ...mapGetters({
      fields: 'field/getAll',
    }),
  },
  created() {
    const keys = Object.keys(this.webhookEventTypes)
    if (keys.length > 0) {
      this.exampleWebhookEventType = this.webhookEventTypes[keys[0]].type
    }

    // If an headers object is provided as default value, we need to populate the
    // internal headers representation that can be edited by this form. When the form
    // is submitted, it will be converted to the correct structure.
    if (this.defaultValues.headers) {
      Object.keys(this.defaultValues.headers).forEach((name) => {
        this.headers.push({
          name,
          value: this.defaultValues.headers[name],
        })
      })
    }
  },
  validations: {
    values: {
      name: { required },
      url: { required, maxLength: maxLength(2000), url },
    },
    headers: {
      $each: {
        name: {
          required,
          valid(value) {
            const regex = /[^:\\s][^:\\r\\n]*$/
            return !!value.match(regex)
          },
        },
        value: {
          required,
        },
      },
    },
  },
  methods: {
    prepareHeaders(headers) {
      const preparedHeaders = {}
      headers.forEach((header) => {
        preparedHeaders[header.name] = header.value
      })
      return preparedHeaders
    },
    getFormValues() {
      const values = form.methods.getFormValues.call(this)
      values.headers = this.prepareHeaders(this.headers)
      return values
    },
    openTestModal() {
      // The form must be valid we can show the test modal.
      if (!this.isFormValid()) {
        this.$v.$touch()
        return
      }

      const values = this.getFormValues()
      this.$refs.testModal.show(
        this.table.id,
        this.exampleWebhookEventType,
        values
      )
    },
    addHeader(name, value) {
      this.headers.push({ name, value })
    },
    removeHeader(index) {
      this.headers.splice(index, 1)
    },
    lastHeader(index) {
      return index === this.headers.length
    },
    convertFromDeprecated() {
      this.values.events = this.values.events.map((eventName) =>
        eventName.replace('row.', 'rows.')
      )
      this.submit()
    },
  },
}
</script>
