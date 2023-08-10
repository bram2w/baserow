<template>
  <Context class="color-picker-context">
    <ColorPicker
      :value="hexColorIncludingAlpha"
      @input=";[colorUpdated($event), $emit('input', $event)]"
    ></ColorPicker>
    <div class="color-picker-context__color">
      <Dropdown
        v-model="type"
        class="dropdown--floating color-picker-context__color-type"
        :show-search="false"
      >
        <DropdownItem name="Hex" :value="COLOR_NOTATIONS.HEX"></DropdownItem>
        <DropdownItem name="RGB" :value="COLOR_NOTATIONS.RGB"></DropdownItem>
      </Dropdown>
      <div v-if="type === 'hex'" class="color-picker-context__color-hex">
        <input
          class="input"
          :value="hexColorExcludingAlpha"
          @input="hexChanged"
        />
      </div>
      <div v-if="type === 'rgb'" class="color-picker-context__color-rgb">
        <input
          type="number"
          min="0"
          max="255"
          :value="r"
          class="input remove-number-input-controls"
          @input="rgbaChanged($event, 'r')"
        />
        <input
          type="number"
          min="0"
          max="255"
          :value="g"
          class="input remove-number-input-controls"
          @input="rgbaChanged($event, 'g')"
        />
        <input
          type="number"
          min="0"
          max="255"
          :value="b"
          class="input remove-number-input-controls"
          @input="rgbaChanged($event, 'b')"
        />
      </div>
      <div class="color-picker-context__color-opacity">
        <div
          class="form-input form-input--with-icon form-input--with-icon-right"
        >
          <input
            type="number"
            min="0"
            max="100"
            class="form-input__input remove-number-input-controls"
            :value="a"
            @input="rgbaChanged($event, 'a')"
          />
          <i class="form-input__icon fas fa-percent"></i>
        </div>
      </div>
    </div>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import ColorPicker from '@baserow/modules/core/components/ColorPicker.vue'
import {
  isValidHexColor,
  convertHexToRgb,
  convertRgbToHex,
} from '@baserow/modules/core/utils/colors'

export const COLOR_NOTATIONS = {
  HEX: 'hex',
  RGB: 'rgb',
}

export const DEFAULT_COLOR_NOTION = COLOR_NOTATIONS.HEX

export default {
  name: 'ColorPickerContext',
  components: { ColorPicker },
  mixins: [context],
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      hexColorIncludingAlpha: '',
      hexColorExcludingAlpha: '',
      r: 0,
      g: 0,
      b: 0,
      a: 0,
      type: DEFAULT_COLOR_NOTION,
    }
  },
  computed: {
    COLOR_NOTATIONS: () => COLOR_NOTATIONS,
  },
  watch: {
    value: {
      handler(value) {
        // Only update the value if it has actually changed because otherwise the user's
        // input can be overwritten from converting to and from hex values.
        if (value !== this.hexColorIncludingAlpha) {
          this.colorUpdated(value)
        }
      },
      immediate: true,
    },
  },
  methods: {
    /**
     * Called whenever the original value is updated. It will make sure that all the
     * variables are updated accordingly if the value is a valid hex color.
     */
    colorUpdated(value) {
      if (!isValidHexColor(value)) {
        return
      }

      const rgba = convertHexToRgb(value)

      this.r = rgba.r * 255
      this.g = rgba.g * 255
      this.b = rgba.b * 255
      this.a = Math.round(rgba.a * 100)

      this.hexColorIncludingAlpha = convertRgbToHex(rgba)

      delete rgba.a
      this.hexColorExcludingAlpha = convertRgbToHex(rgba)
    },
    /**
     * Called when one of the RGBA channels must be updated. This is done via one of the
     * text inputs.
     */
    rgbaChanged(event, channel) {
      const value = parseInt(event.target.value)
      if (isNaN(value) && value >= 0 && value <= 255) {
        return
      }

      const rgba = convertHexToRgb(this.hexColorIncludingAlpha)
      rgba[channel] = value / (channel === 'a' ? 100 : 255)
      const hex = convertRgbToHex(rgba)

      this.colorUpdated(hex)
      this.$emit('input', hex)
    },
    /**
     * Called when one the raw hex value must be updated.
     */
    hexChanged(event) {
      const value = event.target.value
      if (!isValidHexColor(value)) {
        return
      }

      const rgba = convertHexToRgb(this.hexColorIncludingAlpha)
      const newRgba = convertHexToRgb(value)
      rgba.r = newRgba.r
      rgba.g = newRgba.g
      rgba.b = newRgba.b
      const hex = convertRgbToHex(rgba)

      this.colorUpdated(hex)
      // Set the value for `hexColorExcludingAlpha`. That will prevent that the value
      // suddenly changes to something else while typing, which is annoying to the user.
      this.hexColorExcludingAlpha = value

      this.$emit('input', hex)
    },
  },
}
</script>
