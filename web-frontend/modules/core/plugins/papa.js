import Papa from 'papaparse'

export default function (context, inject) {
  Papa.parsePromise = function (file, config = {}) {
    return new Promise((resolve, reject) => {
      Papa.parse(file, { complete: resolve, error: reject, ...config })
    })
  }
  inject('papa', Papa)
}
