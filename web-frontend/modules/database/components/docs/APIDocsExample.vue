<template>
  <div>
    <div v-if="type !== '' && url !== ''" class="api-docs__example">
      <a
        class="api-docs__copy"
        @click.prevent=";[copyToClipboard(url), $refs.urlCopied.show()]"
      >
        Copy
        <Copied ref="urlCopied"></Copied>
      </a>
      <div class="api-docs__example-request">
        <div
          class="api-docs__example-request-type"
          :class="{
            'api-docs__example-request-type--success':
              type.toLowerCase() === 'get',
            'api-docs__example-request-type--primary':
              type.toLowerCase() === 'post',
            'api-docs__example-request-type--warning':
              type.toLowerCase() === 'patch',
            'api-docs__example-request-type--error':
              type.toLowerCase() === 'delete',
          }"
        >
          {{ type | uppercase }}
        </div>
        <div class="api-docs__example-request-url">
          {{ url }}
        </div>
      </div>
    </div>
    <div class="api-docs__example-title">Request sample</div>
    <div class="api-docs__example">
      <a
        class="api-docs__copy"
        @click.prevent="
          ;[copyToClipboard(getFormattedRequest()), $refs.requestCopied.show()]
        "
      >
        Copy
        <Copied ref="requestCopied"></Copied>
      </a>
      <div class="api-docs__example-type">
        <Dropdown :value="value" @input="$emit('input', $event)">
          <DropdownItem value="curl" name="cURL"></DropdownItem>
          <DropdownItem value="http" name="HTTP"></DropdownItem>
          <DropdownItem
            value="javascript"
            name="JavaScript (axios)"
          ></DropdownItem>
          <DropdownItem value="python" name="Python (requests)"></DropdownItem>
        </Dropdown>
      </div>
      <pre
        class="api-docs__example-content"
      ><code>{{ formattedRequest }}</code></pre>
    </div>
    <template v-if="response !== false">
      <div class="api-docs__example-title">Response sample</div>
      <div class="api-docs__example">
        <a
          class="api-docs__copy"
          @click.prevent="
            ;[
              copyToClipboard(getFormattedResponse()),
              $refs.responseCopied.show(),
            ]
          "
        >
          Copy
          <Copied ref="responseCopied"></Copied>
        </a>
        <pre
          class="api-docs__example-content"
        ><code>{{ formattedResponse }}</code></pre>
      </div>
    </template>
  </div>
</template>

<script>
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

export default {
  name: 'APIDocsExample',
  props: {
    value: {
      type: String,
      required: true,
    },
    type: {
      type: String,
      required: false,
      default: 'GET',
    },
    url: {
      type: String,
      required: false,
      default: '',
    },
    request: {
      type: [Object, Boolean],
      required: false,
      default: false,
    },
    response: {
      type: [Object, Boolean],
      required: false,
      default: false,
    },
  },
  computed: {
    formattedResponse() {
      return this.getFormattedResponse()
    },
    formattedRequest() {
      return this.getFormattedRequest()
    },
  },
  methods: {
    format(value) {
      return value !== false ? JSON.stringify(value, null, 4) : ''
    },
    getFormattedRequest() {
      if (this.value === 'curl') {
        return this.getCURLRequestExample()
      } else if (this.value === 'http') {
        return this.getHTTPRequestExample()
      } else if (this.value === 'javascript') {
        return this.getJavaScriptExample()
      } else if (this.value === 'python') {
        return this.getPythonExample()
      }
      return ''
    },
    getCURLRequestExample() {
      let example = 'curl \\'

      if (this.type !== '') {
        example += `\n-X ${this.type} \\`
      }

      example += '\n-H "Authorization: Token YOUR_API_KEY" \\'

      if (this.request !== false) {
        example += '\n-H "Content-Type: application/json" \\'
      }

      example += `\n${this.url}`

      if (this.request !== false) {
        example += ` \\\n--data '${this.format(this.request)}'`
      }

      return example
    },
    getHTTPRequestExample() {
      let example = ''

      if (this.type !== '') {
        example += `${this.type.toUpperCase()} `
      }

      example += `${this.url} HTTP`
      example += '\nAuthorization: Token YOUR_API_KEY'

      if (this.request !== false) {
        example += '\nContent-Type: application/json'
        example += `\n\n${this.format(this.request)}`
      }

      return example
    },
    getJavaScriptExample() {
      let example = 'axios({'

      if (this.type !== '') {
        example += `\n  method: "${this.type.toUpperCase()}",`
      }

      example += `\n  url: "${this.url}",`
      example += '\n  headers: {'
      example += '\n    Authorization: "Token YOUR_API_KEY"'

      if (this.request !== false) {
        example += ',\n    "Content-Type": "application/json"'
      }

      example += '\n  }'

      if (this.request !== false) {
        const data = this.format(this.request).slice(0, -1) + '  }'
        example += `,\n  data: ${data}`
      }

      example += '\n})'
      return example
    },
    getPythonExample() {
      const type = (this.type || 'get').toLowerCase()
      let example = `requests.${type}(`
      example += `\n    "${this.url}",`

      example += '\n    headers={'
      example += `\n        "Authorization": "Token YOUR_API_KEY"`

      if (this.request !== false) {
        example += `,\n        "Content-Type": "application/json"`
      }

      example += '\n    }'

      if (this.request !== false) {
        const data = this.format(this.request).split('\n').join('\n    ')
        example += `,\n    json=${data}`
      }

      example += '\n)'
      return example
    },
    getFormattedResponse() {
      return this.format(this.response)
    },
    copyToClipboard(value) {
      copyToClipboard(value)
    },
  },
}
</script>
