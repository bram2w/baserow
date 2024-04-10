import Vue from 'vue'

import ABButton from '@baserow/modules/builder/components/elements/baseComponents/ABButton'
import ABInput from '@baserow/modules/builder/components/elements/baseComponents/ABInput'
import ABFormGroup from '@baserow/modules/builder/components/elements/baseComponents/ABFormGroup'
import ABLink from '@baserow/modules/builder/components/elements/baseComponents/ABLink'
import ABHeading from '@baserow/modules/builder/components/elements/baseComponents/ABHeading'

function setupVueForAB(Vue) {
  Vue.component('ABButton', ABButton)
  Vue.component('ABInput', ABInput)
  Vue.component('ABFormGroup', ABFormGroup)
  Vue.component('ABLink', ABLink)
  Vue.component('ABHeading', ABHeading)
}

setupVueForAB(Vue)

export { setupVueForAB }
