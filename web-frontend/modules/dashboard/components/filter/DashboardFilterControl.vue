<template>
  <FormGroup
    class="dashboard-filter"
    :class="{ 'dashboard-filter--selected': selected }"
    :label="filter.label"
    small-label
    required
  >
    <Dropdown
      ref="dropdown"
      :class="{ 'dashboard-filter__control--active': appliedValues.length }"
      :tooltip="hasUnavailable ? $t('dashboardFilter.unavailableHelp') : null"
      :before-show="beforeShow"
      @show="onShown"
      @hide="onHidden"
    >
      <template #display>
        <i class="dropdown__selected-icon iconoir-filter" />
        <span
          class="dropdown__selected-text dashboard-filter__value"
          :class="{ 'dropdown__selected-placeholder': !appliedValues.length }"
          >{{
            appliedValues.length > 1
              ? $t('dashboardFilter.selections', {
                  count: appliedValues.length,
                })
              : (appliedValues[0] && optionLabel(appliedValues[0])) ||
                $t('dashboardFilter.choose')
          }}</span
        >
        <i
          v-if="hasUnavailable"
          class="iconoir-info-empty dashboard-filter__info"
          :aria-label="$t('dashboardFilter.unavailable')"
        />
      </template>
      <template
        v-if="(editMode && canDelete) || (!editMode && appliedValues.length)"
        #suffix
      >
        <ButtonIcon
          v-if="editMode"
          ref="menuTrigger"
          class="dashboard-filter__action"
          type="secondary"
          size="small"
          icon="iconoir-more-vert"
          :aria-label="$t('dashboardFilter.actions')"
          :aria-expanded="menuOpen"
          :disabled="deleting"
          :loading="deleting"
          @click.stop="toggleMenu"
        />
        <ButtonIcon
          v-else
          class="dashboard-filter__action"
          type="secondary"
          size="small"
          icon="iconoir-cancel"
          :aria-label="$t('dashboardFilter.clear')"
          @click="$emit('apply', [])"
        />
      </template>
      <template #content>
        <div
          class="dashboard-filter__context"
          :class="{
            'dashboard-filter__context--dropdown': filter.mode === 'dropdown',
          }"
        >
          <form @submit.prevent="apply">
            <template v-if="filter.mode === 'dropdown'">
              <SelectSearch
                v-model="search"
                :aria-label="$t('action.search')"
              />
              <div class="dashboard-filter__choices">
                <div
                  v-for="value in displayedOptions"
                  :key="value"
                  class="dashboard-filter__choice"
                  :class="{
                    'dashboard-filter__choice--single': !filter.multiple,
                  }"
                >
                  <Checkbox
                    v-if="filter.multiple"
                    :model-value="draft.includes(value)"
                    @update:model-value="toggle(value, $event)"
                  >
                    <span class="dashboard-filter__option-value">{{
                      optionLabel(value)
                    }}</span>
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
                    <span class="dashboard-filter__option-value">{{
                      optionLabel(value)
                    }}</span>
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
                  <Button
                    type="secondary"
                    size="small"
                    button-type="button"
                    @click="requestOptions()"
                    >{{ $t('action.retry') }}</Button
                  >
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
                  button-type="button"
                  @click="requestOptions(true)"
                  >{{ $t('dashboardFilter.more') }}</Button
                >
              </div>
            </template>
            <div v-else class="dashboard-filter__input">
              <FormGroup :label="filter.label" small-label required>
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
        </div>
      </template>
    </Dropdown>
    <Context
      v-if="editMode && canDelete"
      ref="menu"
      overflow-scroll
      max-height-if-outside-viewport
      @shown="focusDelete"
      @hidden="menuOpen = false"
      @keydown.esc.prevent.stop="closeMenu"
    >
      <ul class="context__menu">
        <li class="context__menu-item">
          <button
            ref="deleteOption"
            type="button"
            class="context__menu-item-link context__menu-item-link--delete dashboard-filter__menu-option"
            :disabled="deleting"
            @click="remove"
          >
            <i class="context__menu-item-icon iconoir-bin" />
            {{ $t('dashboardFilter.delete') }}
          </button>
        </li>
      </ul>
    </Context>
  </FormGroup>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import FormInput from '@baserow/modules/core/components/FormInput'
import FormGroup from '@baserow/modules/core/components/FormGroup'
import Button from '@baserow/modules/core/components/Button'
import ButtonIcon from '@baserow/modules/core/components/ButtonIcon'
import SelectSearch from '@baserow/modules/core/components/SelectSearch'
import Context from '@baserow/modules/core/components/Context'
import { shouldResetFilterValues } from '@baserow/modules/dashboard/utils/filter'

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
  canDelete: Boolean,
  deleting: Boolean,
})
const emit = defineEmits(['apply', 'select', 'options', 'delete'])
const dropdown = ref(null)
const input = ref(null)
const menu = ref(null)
const menuTrigger = ref(null)
const deleteOption = ref(null)
const menuOpen = ref(false)
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
const optionLabel = (value) => props.optionState.labels?.[value] || value
const displayedOptions = computed(() => {
  const query = search.value.toLowerCase()
  return [...new Set([...props.optionState.results, ...draft.value])].filter(
    (value) =>
      value.toLowerCase().includes(query) ||
      optionLabel(value).toLowerCase().includes(query)
  )
})
const hasUnavailable = computed(() =>
  props.appliedValues.some((value) =>
    props.optionState.unavailable.includes(value)
  )
)
const requestOptions = (more = false, useCache = false) =>
  emit('options', {
    more,
    selected: [...new Set([...props.appliedValues, ...draft.value])],
    ...(useCache ? { useCache: true } : {}),
  })

watch(
  () => props.filter,
  (filter, previous) => {
    if (!shouldResetFilterValues(previous, filter)) return
    draft.value = []
    search.value = ''
    dropdown.value?.hide()
  }
)

function beforeShow() {
  if (props.editMode) {
    emit('select')
    return false
  }
}
function toggleMenu(event) {
  if (!props.deleting) {
    menu.value.toggle(event.currentTarget, 'bottom', 'right', 8, -8)
  }
}
async function focusDelete() {
  menuOpen.value = true
  await nextTick()
  deleteOption.value?.focus()
}
function closeMenu() {
  menu.value.hide()
  menuTrigger.value?.$el.focus()
}
function remove() {
  if (!props.editMode || !props.canDelete || props.deleting) return
  closeMenu()
  emit('delete')
}
async function onShown() {
  draft.value = [...props.appliedValues]
  search.value = ''
  if (props.filter.mode === 'dropdown') requestOptions(false, true)
  await nextTick()
  input.value?.focus()
}
function onHidden() {
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
  dropdown.value.close()
}
</script>
