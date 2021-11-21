<template>
  <form @submit.prevent="submit" @input="$emit('formchange')">
    <div
      v-if="!values.active"
      class="alert alert--simple alert--primary alert--has-icon"
    >
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">{{ $t('webhookForm.deactivated.title') }}</div>
      <p class="alert__content">
        {{ $t('webhookForm.deactivated.content') }}
      </p>
      <a
        class="button button--ghost margin-top-1"
        @click="values.active = true"
        >{{ $t('webhookForm.deactivated.activate') }}</a
      >
    </div>
    <div class="row">
      <div class="col col-12">
        <div class="control">
          <label class="control__label">
            {{ $t('webhookForm.inputLabels.name') }}
          </label>
          <div class="control__elements">
            <input
              v-model="values.name"
              class="input"
              :class="{ 'input--error': $v.values.name.$error }"
              @blur="$v.values.name.$touch()"
            />
            <div v-if="$v.values.name.$error" class="error">
              {{ $t('error.requiredField') }}
            </div>
          </div>
        </div>
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
        <div class="control">
          <label class="control__label">
            {{ $t('webhookForm.inputLabels.url') }}
          </label>
          <div class="control__elements">
            <input
              v-model="values.url"
              class="input"
              :class="{ 'input--error': $v.values.url.$error }"
              @blur="$v.values.url.$touch()"
            />
            <div v-if="$v.values.url.$error" class="error">
              {{ $t('webhookForm.errors.urlField') }}
            </div>
          </div>
        </div>
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
              placeholder="Name"
              @input="lastHeader(index) && addHeader(header.name, header.value)"
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
              placeholder="Value"
              @input="lastHeader(index) && addHeader(header.name, header.value)"
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
  </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { required } from 'vuelidate/lib/validators'

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
      fields: 'field/getAllWithPrimary',
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
      url: { required },
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
  },
}
</script>

<i18n>
{
  "en": {
    "webhookForm": {
      "inputLabels": {
        "name": "Name",
        "requestMethod": "Method",
        "url": "URL",
        "userFieldNames": "User field names",
        "events": "Which events should trigger this webhook?",
        "headers": "Additional headers",
        "example": "Example payload"
      },
      "errors": {
        "urlField": "This field is required and needs to be a valid url.",
        "invalidHeaders": "One of the headers is invalid."
      },
      "checkbox": {
        "sendUserFieldNames": "Use field name instead of id"
      },
      "radio": {
        "allEvents": "Send me everything",
        "customEvents": "Let me select individual events"
      },
      "triggerButton": "Trigger test webhook",
      "deactivated": {
        "title": "Webhook is deactivated",
        "content": "This webhook has been deactivated because there have been too many consecutive failures. Please check the call log for more details. Click on the button below to activate it again. Don't forgot to save the webhook after activating.",
        "activate": "Activate"
      }
    }
  },
  "fr": {
    "webhookForm": {
      "inputLabels": {
        "name": "@TODO",
        "requestMethod": "@TODO",
        "url": "@TODO",
        "userFieldNames": "@TODO",
        "events": "@TODO",
        "headers": "@TODO",
        "example": "@TODO"
      },
      "errors": {
        "urlField": "@TODO",
        "invalidHeaders": "@TODO"
      },
      "checkbox": {
        "sendUserFieldNames": "@TODO"
      },
      "radio": {
        "allEvents": "@TODO",
        "customEvents": "@TODO"
      },
      "triggerButton": "@TODO",
      "deactivated": {
        "title": "@TODO",
        "content": "@TODO",
        "activate": "@TODO"
      }
    }
  }
}
</i18n>
