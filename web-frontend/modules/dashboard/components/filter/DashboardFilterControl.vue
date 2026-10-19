<template>
  <div
    class="dashboard-filter"
    :class="{ 'dashboard-filter--selected': selected }"
  >
    <label class="dashboard-filter__label" :for="controlId">{{
      filter.label
    }}</label>
    <div
      class="dashboard-filter__control"
      :class="{ 'dashboard-filter__control--active': appliedValues.length }"
    >
      <Button
        :id="controlId"
        ref="trigger"
        v-tooltip.focus="
          hasUnavailable ? $t('dashboardFilter.unavailableHelp') : null
        "
        class="dashboard-filter__trigger"
        type="secondary"
        button-type="button"
        icon="iconoir-filter"
        :aria-expanded="opened"
        :aria-description="
          hasUnavailable ? $t('dashboardFilter.unavailableHelp') : undefined
        "
        @click="activate"
      >
        <span class="dashboard-filter__value">{{
          appliedValues.length > 1
            ? $t('dashboardFilter.selections', { count: appliedValues.length })
            : appliedValues[0] || $t('dashboardFilter.choose')
        }}</span>
        <i
          v-if="hasUnavailable"
          class="iconoir-info-empty dashboard-filter__info"
          :aria-label="$t('dashboardFilter.unavailable')"
        ></i>
      </Button>
      <ButtonIcon
        v-if="editMode"
        class="dashboard-filter__action"
        type="secondary"
        size="small"
        icon="iconoir-more-vert"
        :aria-label="$t('dashboardFilter.settings')"
        @click="$emit('select')"
      />
      <ButtonIcon
        v-else-if="appliedValues.length"
        class="dashboard-filter__action"
        type="secondary"
        size="small"
        icon="iconoir-cancel"
        :aria-label="$t('dashboardFilter.clear')"
        @click="$emit('apply', [])"
      />
      <i
        v-else
        class="iconoir-nav-arrow-down dashboard-filter__arrow"
        aria-hidden="true"
      ></i>
    </div>
    <Context
      ref="context"
      class="dashboard-filter__context"
      :class="{
        'dashboard-filter__context--dropdown': filter.mode === 'dropdown',
      }"
      @shown="onShown"
      @hidden="onHidden"
    >
      <form @submit.prevent="apply" @keydown.esc.stop.prevent="close">
        <template v-if="filter.mode === 'dropdown'">
          <SelectSearch
            v-model="search"
            :aria-label="$t('action.search')"
            @update:model-value="searchOptions"
          />
          <div class="dashboard-filter__operator">
            {{ $t(`dashboardFilter.${filter.operator}`) }}...
          </div>
          <div class="dashboard-filter__choices">
            <div
              v-for="value in displayedOptions"
              :key="value"
              class="dashboard-filter__choice"
              :class="{ 'dashboard-filter__choice--single': !filter.multiple }"
            >
              <Checkbox
                v-if="filter.multiple"
                :model-value="draft.includes(value)"
                @update:model-value="toggle(value, $event)"
              >
                <span class="dashboard-filter__option-value">{{ value }}</span>
              </Checkbox>
              <Button
                v-else
                type="secondary"
                button-type="button"
                full-width
                :append-icon="draft.includes(value) ? 'iconoir-check' : ''"
                class="dashboard-filter__single-choice"
                :aria-pressed="draft.includes(value)"
                @click="toggle(value, !draft.includes(value))"
              >
                <span class="dashboard-filter__option-value">{{ value }}</span>
              </Button>
              <span
                v-if="optionState.unavailable.includes(value)"
                v-tooltip.focus="$t('dashboardFilter.unavailableHelp')"
                class="dashboard-filter__unavailable"
                tabindex="0"
                :aria-label="$t('dashboardFilter.unavailableHelp')"
                >{{ $t('dashboardFilter.unavailable') }}</span
              >
            </div>
            <div
              v-if="optionState.loading"
              class="dashboard-filter__message"
              role="status"
            >
              {{ $t('dashboardFilter.loading') }}
            </div>
            <div
              v-else-if="optionState.error"
              class="dashboard-filter__message"
              role="status"
            >
              {{ $t('dashboardFilter.optionsError') }}
              <Button type="secondary" size="small" @click="requestOptions()">{{
                $t('action.retry')
              }}</Button>
            </div>
            <div
              v-else-if="!displayedOptions.length"
              class="dashboard-filter__message"
            >
              {{ $t('dashboardFilter.noOptions') }}
            </div>
            <Button
              v-if="optionState.next && !optionState.loading"
              type="secondary"
              size="small"
              class="dashboard-filter__more"
              @click="requestOptions(true)"
              >{{ $t('dashboardFilter.more') }}</Button
            >
          </div>
        </template>
        <div v-else class="dashboard-filter__input">
          <FormGroup
            :label="`${$t(`dashboardFilter.${filter.operator}`)}...`"
            small-label
            required
          >
            <FormInput
              ref="input"
              :model-value="draft[0] || ''"
              :placeholder="$t('dashboardFilter.inputPlaceholder')"
              :maxlength="10000"
              @update:model-value="draft = [$event]"
            />
          </FormGroup>
        </div>
        <div class="dashboard-filter__footer">
          <Button :disabled="!changed" button-type="submit">{{
            $t(
              appliedValues.length
                ? 'dashboardFilter.update'
                : 'dashboardFilter.apply'
            )
          }}</Button>
        </div>
      </form>
    </Context>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, useId } from 'vue'
import debounce from 'lodash/debounce'
import Context from '@baserow/modules/core/components/Context'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import FormInput from '@baserow/modules/core/components/FormInput'
import FormGroup from '@baserow/modules/core/components/FormGroup'
import Button from '@baserow/modules/core/components/Button'
import ButtonIcon from '@baserow/modules/core/components/ButtonIcon'
import SelectSearch from '@baserow/modules/core/components/SelectSearch'

const props = defineProps({
  filter: { type: Object, required: true },
  appliedValues: { type: Array, default: () => [] },
  optionState: {
    type: Object,
    default: () => ({
      results: [],
      unavailable: [],
      next: null,
      loading: false,
      error: false,
    }),
  },
  editMode: Boolean,
  selected: Boolean,
})
const emit = defineEmits(['apply', 'select', 'options'])
const controlId = `dashboard-filter-${useId()}`
const context = ref(null)
const trigger = ref(null)
const input = ref(null)
const opened = ref(false)
const draft = ref([])
const search = ref('')
const normalizedDraft = computed(() =>
  props.filter.mode === 'input'
    ? draft.value.map((value) => value.trim()).filter(Boolean)
    : draft.value
)
const changed = computed(
  () =>
    JSON.stringify(normalizedDraft.value) !==
    JSON.stringify(props.appliedValues)
)
const displayedOptions = computed(() => [
  ...new Set([...draft.value, ...props.optionState.results]),
])
const hasUnavailable = computed(() =>
  props.appliedValues.some((value) =>
    props.optionState.unavailable.includes(value)
  )
)
const requestOptions = (more = false) =>
  emit('options', {
    search: search.value,
    more,
    selected: [...new Set([...props.appliedValues, ...draft.value])],
  })
const searchOptions = debounce(() => {
  if (opened.value) requestOptions()
}, 250)

function activate(event) {
  if (props.editMode) emit('select')
  else context.value.toggle(event.currentTarget, 'bottom', 'left', 4)
}
async function onShown() {
  opened.value = true
  draft.value = [...props.appliedValues]
  search.value = ''
  if (props.filter.mode === 'dropdown') requestOptions()
  await nextTick()
  input.value?.focus()
}
function onHidden() {
  opened.value = false
  searchOptions.cancel()
  draft.value = [...props.appliedValues]
}
function toggle(value, checked) {
  draft.value = checked
    ? props.filter.multiple
      ? [...draft.value, value]
      : [value]
    : draft.value.filter((item) => item !== value)
}
function apply() {
  if (!changed.value) return
  emit('apply', [...normalizedDraft.value])
  close()
}
function close() {
  context.value.hide()
  trigger.value?.focus()
}
onBeforeUnmount(() => searchOptions.cancel())
</script>
