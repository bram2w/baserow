import Vue from 'vue'

import Context from '@/components/Context'
import Modal from '@/components/Modal'
import Editable from '@/components/Editable'
import Dropdown from '@/components/Dropdown'
import DropdownItem from '@/components/DropdownItem'
import Checkbox from '@/components/Checkbox'
import Scrollbars from '@/components/Scrollbars'

import lowercase from '@/filters/lowercase'

import scroll from '@/directives/scroll'

Vue.component('Context', Context)
Vue.component('Modal', Modal)
Vue.component('Editable', Editable)
Vue.component('Dropdown', Dropdown)
Vue.component('DropdownItem', DropdownItem)
Vue.component('Checkbox', Checkbox)
Vue.component('Scrollbars', Scrollbars)

Vue.filter('lowercase', lowercase)

Vue.directive('scroll', scroll)
