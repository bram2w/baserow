import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import { ref } from 'vue'
import Button from '@baserow/modules/core/components/Button'
import ButtonIcon from '@baserow/modules/core/components/ButtonIcon'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import FormGroup from '@baserow/modules/core/components/FormGroup'
import FormInput from '@baserow/modules/core/components/FormInput'

export default {
  title: 'Baserow/Form Elements/Dropdown',
  component: Dropdown,
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: 'text',
      description: 'Selected value (v-model)',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text when empty',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable the dropdown',
    },
    loading: {
      control: 'boolean',
      description: 'Show a spinner and prevent opening the dropdown',
    },
    showSearch: {
      control: 'boolean',
      description: 'Show search input inside dropdown',
    },
    searchText: {
      control: 'text',
      description: 'Search input value',
    },
    showFooter: {
      control: 'boolean',
      description: 'Show footer slot',
    },
    size: {
      control: 'select',
      options: ['regular', 'large', 'small'],
      description: 'Size of the dropdown',
    },
    fixedItems: {
      control: 'boolean',
      description: 'Use fixed positioning for items',
    },
    error: {
      control: 'boolean',
      description: 'Show error state',
    },
  },
  args: {
    value: '',
    placeholder: 'Select an option',
    disabled: false,
    loading: false,
    showSearch: false,
    searchText: '',
    showFooter: false,
    size: 'regular',
    fixedItems: false,
    error: false,
  },
}

export const Default = {
  render: (args) => ({
    components: { Dropdown, DropdownItem },
    setup() {
      return { args }
    },
    template: `
      <div style="height: 250px;">
        <Dropdown v-bind="args">
          <DropdownItem name="Option 1" value="1" />
          <DropdownItem name="Option 2" value="2" />
          <DropdownItem name="Option 3" value="3" />
        </Dropdown>
      </div>
    `,
  }),
}

export const WithSearch = {
  args: {
    showSearch: true,
    placeholder: 'Search country...',
  },
  render: (args) => ({
    components: { Dropdown, DropdownItem },
    setup() {
      return { args }
    },
    template: `
      <div style="height: 300px;">
        <Dropdown v-bind="args">
          <DropdownItem name="France" value="fr" />
          <DropdownItem name="Germany" value="de" />
          <DropdownItem name="Italy" value="it" />
          <DropdownItem name="Spain" value="es" />
          <DropdownItem name="United Kingdom" value="uk" />
        </Dropdown>
      </div>
    `,
  }),
}

export const Disabled = {
  args: {
    disabled: true,
    value: '1',
  },
  render: (args) => ({
    components: { Dropdown, DropdownItem },
    setup() {
      return { args }
    },
    template: `
      <Dropdown v-bind="args">
        <DropdownItem name="Option 1" value="1" />
      </Dropdown>
    `,
  }),
}

export const WithFooter = {
  args: {
    showFooter: true,
  },
  render: (args) => ({
    components: { Dropdown, DropdownItem },
    setup() {
      return { args }
    },
    template: `
      <div style="height: 250px;">
        <Dropdown v-bind="args">
          <DropdownItem name="Option A" value="a" />
          <DropdownItem name="Option B" value="b" />
          <template #footer>
              Custom Footer Content
          </template>
        </Dropdown>
      </div>
    `,
  }),
}

export const WithApply = {
  parameters: {
    controls: { include: ['disabled', 'loading', 'size', 'error'] },
    docs: {
      description: {
        story:
          'The display slot customizes the trigger; content replaces the item list with a positioned panel. The caller owns the draft and commits it on Apply, then calls the scoped close function. Clicking outside or pressing Escape discards the draft. The suffix slot keeps Clear separate from the trigger. Item-list props such as showSearch and multiple do not control custom content.',
      },
    },
  },
  render: (args) => ({
    components: { Dropdown, Button, ButtonIcon, Checkbox, FormGroup },
    setup() {
      const applied = ref([])
      const draft = ref([])
      const resetDraft = () => {
        draft.value = [...applied.value]
      }
      const toggle = (country, checked) => {
        draft.value = checked
          ? [...draft.value, country]
          : draft.value.filter((value) => value !== country)
      }
      const apply = (close) => {
        applied.value = [...draft.value]
        close()
      }
      return {
        args,
        applied,
        draft,
        resetDraft,
        toggle,
        apply,
        countries: ['France', 'Germany', 'Italy'],
      }
    },
    template: `
      <div style="max-width: 360px; min-height: 400px;">
        <FormGroup label="Country" required small-label>
          <Dropdown v-bind="args" @show="resetDraft" @hide="resetDraft">
            <template #display>
              <i class="dropdown__selected-icon iconoir-filter" />
              <span :class="applied.length ? 'dropdown__selected-text' : 'dropdown__selected-placeholder'">
                {{ applied.length ? applied.join(', ') : 'Choose...' }}
              </span>
            </template>
            <template v-if="applied.length" #suffix>
              <ButtonIcon icon="iconoir-cancel" type="secondary" size="small"
                aria-label="Clear countries" :disabled="args.disabled || args.loading"
                @click="applied = []" />
            </template>
            <template #content="{ close }">
              <form class="context__form" @submit.prevent="apply(close)">
                <div class="context__form-container">
                  <Checkbox v-for="country in countries" :key="country"
                    :model-value="draft.includes(country)"
                    @update:model-value="toggle(country, $event)">
                    {{ country }}
                  </Checkbox>
                  <div class="context__form-footer-actions">
                    <Button button-type="submit"
                      :disabled="JSON.stringify(applied) === JSON.stringify(draft)">Apply</Button>
                  </div>
                </div>
              </form>
            </template>
          </Dropdown>
        </FormGroup>
        <p class="margin-top-2" role="status">Applied: {{ applied.join(', ') || 'All countries' }}</p>
        <p>Choose countries, then Apply. Click outside or press Escape to cancel.</p>
      </div>
    `,
  }),
}

export const WithInput = {
  parameters: {
    controls: { include: ['disabled', 'loading', 'size', 'error'] },
    docs: {
      description: {
        story:
          'Custom content can also be an input form. Typing only changes the draft. Apply or Enter commits it; Escape or an outside click cancels it. Closing via the scoped close function restores focus to the Dropdown trigger.',
      },
    },
  },
  render: (args) => ({
    components: { Dropdown, Button, FormGroup, FormInput },
    setup() {
      const applied = ref('')
      const draft = ref('')
      const input = ref(null)
      const open = () => {
        draft.value = applied.value
        input.value?.focus()
      }
      const apply = (close) => {
        applied.value = draft.value.trim()
        close()
      }
      return { args, applied, draft, input, open, apply }
    },
    template: `
      <div style="max-width: 360px; min-height: 300px;">
        <FormGroup label="Country" required small-label>
          <Dropdown v-bind="args" @show="open" @hide="draft = applied">
            <template #display>
              <i class="dropdown__selected-icon iconoir-filter" />
              <span :class="applied ? 'dropdown__selected-text' : 'dropdown__selected-placeholder'">
                {{ applied || 'Choose...' }}
              </span>
            </template>
            <template #content="{ close }">
              <form class="context__form" @submit.prevent="apply(close)">
                <div class="context__form-container">
                  <FormGroup label="Is..." required small-label>
                    <FormInput ref="input" v-model="draft" placeholder="Enter a country" />
                  </FormGroup>
                  <div class="context__form-footer-actions">
                    <Button button-type="submit" :disabled="draft.trim() === applied">Apply</Button>
                  </div>
                </div>
              </form>
            </template>
          </Dropdown>
        </FormGroup>
        <p class="margin-top-2" role="status">Applied: {{ applied || 'All countries' }}</p>
        <p>Type a country, then Apply or press Enter. Escape cancels your changes.</p>
      </div>
    `,
  }),
}
