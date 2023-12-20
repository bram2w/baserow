<template>
  <div class="form-view__meta-controls">
    <div
      v-if="
        !readOnly &&
        $hasPermission(
          'database.table.view.update',
          view,
          database.workspace.id
        )
      "
      class="control form-view__control-notification-on-submit"
    >
      <SwitchInput
        class=""
        :value="view.receive_notification_on_submit"
        @input="
          $emit('updated-form', { receive_notification_on_submit: $event })
        "
      ></SwitchInput>
      {{ $t('formSidebar.notifyUserOnSubmit') }}
    </div>
    <div class="control">
      <label class="control__label">When the form is submitted</label>
      <div class="control__elements">
        <ul class="choice-items choice-items--inline">
          <li>
            <a
              class="choice-items__link"
              :class="{
                active: view.submit_action === 'MESSAGE',
                disabled: readOnly,
              }"
              @click="
                !readOnly &&
                  view.submit_action !== 'MESSAGE' &&
                  $emit('updated-form', { submit_action: 'MESSAGE' })
              "
              ><span>Show a message</span>
              <i
                v-if="view.submit_action === 'MESSAGE'"
                class="choice-items__icon-active iconoir-check-circle"
              ></i
            ></a>
          </li>
          <li>
            <a
              class="choice-items__link"
              :class="{
                active: view.submit_action === 'REDIRECT',
                disabled: readOnly,
              }"
              @click="
                !readOnly &&
                  view.submit_action !== 'REDIRECT' &&
                  $emit('updated-form', { submit_action: 'REDIRECT' })
              "
              ><span>Redirect to URL</span>
              <i
                v-if="view.submit_action === 'REDIRECT'"
                class="choice-items__icon-active iconoir-check-circle"
              ></i
            ></a>
          </li>
        </ul>
      </div>
    </div>
    <div v-if="view.submit_action === 'MESSAGE'" class="control">
      <label class="control__label">The message</label>
      <div class="control__elements">
        <textarea
          v-model="submit_action_message"
          type="text"
          class="input form-view__meta-message-textarea"
          placeholder="The message"
          rows="3"
          :disabled="readOnly"
          @blur="
            $emit('updated-form', {
              submit_action_message,
            })
          "
        />
      </div>
    </div>
    <div v-if="view.submit_action === 'REDIRECT'" class="control">
      <label class="control__label">The URL</label>
      <div class="control__elements">
        <input
          v-model="submit_action_redirect_url"
          type="text"
          class="input"
          placeholder="The URL"
          :disabled="readOnly"
          @blur="
            ;[
              $v.submit_action_redirect_url.$touch(),
              !$v.submit_action_redirect_url.$error &&
                $emit('updated-form', {
                  submit_action_redirect_url,
                }),
            ]
          "
        />
        <div v-if="$v.submit_action_redirect_url.$error" class="error">
          Please enter a valid URL
        </div>
      </div>
      <div class="form-view__meta-controls-help">
        {{ $t('formViewMeta.includeRowId') }}
      </div>
    </div>
  </div>
</template>

<script>
import { required, url } from 'vuelidate/lib/validators'

export default {
  name: 'FormViewMetaControls',
  props: {
    view: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      submit_action_message: '',
      submit_action_redirect_url: '',
    }
  },
  watch: {
    'view.submit_action_message'(value) {
      this.submit_action_message = value
    },
    'view.submit_action_redirect_url'(value) {
      this.submit_action_redirect_url = value
    },
  },
  created() {
    this.submit_action_message = this.view.submit_action_message
    this.submit_action_redirect_url = this.view.submit_action_redirect_url
  },
  validations: {
    submit_action_redirect_url: { required, url },
  },
}
</script>
