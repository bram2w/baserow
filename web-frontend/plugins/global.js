import Vue from 'vue'

import Context from '@/components/Context'
import Modal from '@/components/Modal'
import Editable from '@/components/Editable'
import Dropdown from '@/components/Dropdown'
import DropdownItem from '@/components/DropdownItem'
import Checkbox from '@/components/Checkbox'

import lowercase from '@/filters/lowercase'

Vue.component('Context', Context)
Vue.component('Modal', Modal)
Vue.component('Editable', Editable)
Vue.component('Dropdown', Dropdown)
Vue.component('DropdownItem', DropdownItem)
Vue.component('Checkbox', Checkbox)

Vue.filter('lowercase', lowercase)
