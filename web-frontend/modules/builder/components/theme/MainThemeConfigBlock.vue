<template>
  <div>
    <ColorPickerContext
      ref="colorPicker"
      :value="builder.theme[colorPickerPropertyName] || '#000000ff'"
      @input="colorPickerColorChanged"
    ></ColorPickerContext>
    <div class="theme_settings__section margin-bottom-3">
      <div class="theme_settings__section-properties">
        <a
          class="theme_settings__section-title"
          @click="toggleClosed('colors')"
        >
          {{ $t('mainThemeConfigBlock.colorsLabel') }}
          <i
            class="iconoir-nav-arrow-down theme_settings__section-title-icon"
            :class="{
              'theme_settings__section-title-icon': true,
              'iconoir-nav-arrow-down': !isClosed('colors'),
              'iconoir-nav-arrow-right': isClosed('colors'),
            }"
          ></i>
        </a>
        <div v-show="!isClosed('colors')">
          <ColorInputGroup
            :value="builder.theme.primary_color"
            label-after
            :label="$t('mainThemeConfigBlock.primaryColor')"
            @input="setPropertyInStore('primary_color', $event)"
          />
          <ColorInputGroup
            :value="builder.theme.secondary_color"
            label-after
            :label="$t('mainThemeConfigBlock.secondaryColor')"
            @input="setPropertyInStore('secondary_color', $event)"
          />
        </div>
      </div>
    </div>
    <div>
      <div class="theme_settings__section">
        <div class="theme_settings__section-properties">
          <a
            class="theme_settings__section-title"
            @click="toggleClosed('typography')"
          >
            {{ $t('mainThemeConfigBlock.typography') }}
            <i
              class="iconoir-nav-arrow-down theme_settings__section-title-icon"
              :class="{
                'theme_settings__section-title-icon': true,
                'iconoir-nav-arrow-down': !isClosed('typography'),
                'iconoir-nav-arrow-right': isClosed('typography'),
              }"
            ></i>
          </a>
        </div>
      </div>
      <div
        v-for="i in headings"
        v-show="!isClosed('typography')"
        :key="i"
        class="theme_settings__section"
      >
        <div class="theme_settings__section-properties">
          <div class="control">
            <div class="control__label">
              {{ $t('mainThemeConfigBlock.headingLabel', { i }) }}
            </div>
            <div class="control__elements control__elements--flex">
              <ColorInput
                :value="builder.theme[`heading_${i}_color`]"
                @input="setPropertyInStore(`heading_${i}_color`, $event)"
              />
              <div class="input__with-icon">
                <input
                  type="number"
                  class="input remove-number-input-controls"
                  :min="fontSizeMin"
                  :max="fontSizeMax"
                  :class="{
                    'input--error':
                      $v.builder.theme[`heading_${i}_font_size`].$error,
                  }"
                  :value="builder.theme[`heading_${i}_font_size`]"
                  @input="
                    ;[
                      $v.builder.theme[`heading_${i}_font_size`].$touch(),
                      setPropertyInStore(
                        `heading_${i}_font_size`,
                        $event.target.value,
                        !$v.builder.theme[`heading_${i}_font_size`].$error
                      ),
                    ]
                  "
                />
                <i>px</i>
              </div>
            </div>
            <div
              v-if="$v.builder.theme[`heading_${i}_font_size`].$error"
              class="error"
            >
              {{ $t('error.minMaxLength', { min: 1, max: 100 }) }}
            </div>
          </div>
        </div>
        <div class="theme_settings__section-preview">
          <component
            :is="`h${i}`"
            class="margin-bottom-2 theme_settings__section-ellipsis"
            :class="`ab-heading--h${i}`"
            :style="{
              [`--heading-h${i}--color`]: builder.theme[`heading_${i}_color`],
              [`--heading-h${i}--font-size`]:
                builder.theme[`heading_${i}_font_size`] + 'px',
            }"
          >
            {{ $t('mainThemeConfigBlock.headingValue', { i }) }}
          </component>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'
import ColorPickerContext from '@baserow/modules/core/components/ColorPickerContext'
import { notifyIf } from '@baserow/modules/core/utils/error'

const fontSizeMin = 1
const fontSizeMax = 100
const headings = [1, 2, 3]

export default {
  name: 'MainThemeConfigBlock',
  components: { ColorPickerContext },
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      closed: [],
      colorPickerPropertyName: '',
    }
  },
  computed: {
    headings() {
      return headings
    },
    fontSizeMin() {
      return fontSizeMin
    },
    fontSizeMax() {
      return fontSizeMax
    },
  },
  methods: {
    ...mapActions({
      setThemeProperty: 'theme/setProperty',
      forceSetThemeProperty: 'theme/forceSetProperty',
    }),
    toggleClosed(value) {
      const index = this.closed.indexOf(value)
      if (index < 0) {
        this.closed.push(value)
      } else {
        this.closed.splice(index, 1)
      }
    },
    isClosed(value) {
      return this.closed.includes(value)
    },
    openColorPicker(opener, propertyName) {
      this.colorPickerPropertyName = propertyName
      this.$refs.colorPicker.toggle(opener)
    },
    colorPickerColorChanged(value) {
      this.setPropertyInStore(this.colorPickerPropertyName, value)
    },
    async setPropertyInStore(key, value, makeRequest = true) {
      const action = makeRequest ? 'setThemeProperty' : 'forceSetThemeProperty'

      try {
        await this[action]({
          builder: this.builder,
          key,
          value,
        })
      } catch (error) {
        notifyIf(error, 'row')
      }
    },
  },
  validations: {
    builder: {
      theme: headings.reduce((o, i) => {
        o[`heading_${i}_font_size`] = {
          required,
          integer,
          minValue: minValue(fontSizeMin),
          maxValue: maxValue(fontSizeMax),
        }
        return o
      }, {}),
    },
  },
}
</script>
