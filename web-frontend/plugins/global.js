import Vue from 'vue'

import Context from '@/components/Context'
import Modal from '@/components/Modal'
import Editable from '@/components/Editable'

import lowercase from '@/filters/lowercase'

Vue.component('Context', Context)
Vue.component('Modal', Modal)
Vue.component('Editable', Editable)

Vue.filter('lowercase', lowercase)
