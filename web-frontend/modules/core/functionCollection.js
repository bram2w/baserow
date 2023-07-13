import { FunctionCollection } from '@baserow/formula/parser/javascriptExecutor'

export class RuntimeFunctionCollection extends FunctionCollection {
  constructor($registry) {
    super()
    this.$registry = $registry
  }

  get(name) {
    return this.$registry.get('runtime_formula_type', name)
  }
}
