import _ from 'lodash/fp'

export class FromTipTapVisitor {
  constructor(functions) {
    this.functions = functions
  }

  visit(content) {
    if (_.isArray(content)) {
      return this.visitArray(content)
    } else {
      return this.visitNode(content)
    }
  }

  visitNode(node) {
    switch (node.type) {
      case 'text':
        return this.visitText(node)
      case 'hardBreak':
        return this.visitHardBreak(node)
      default:
        return this.visitFunction(node)
    }
  }

  visitArray(content) {
    if (content.length === 0) {
      return ''
    }

    if (content.length === 1) {
      return this.visit(content[0])
    }

    return `concat(${content.map(this.visit.bind(this)).join(', ')})`
  }

  visitText(node) {
    return `'${node.text.replace(/'/g, "\\'")}'`
  }

  visitHardBreak(node) {
    return "'\n'"
  }

  visitFunction(node) {
    const formulaFunction = Object.values(this.functions.getAll()).find(
      (functionCurrent) => functionCurrent.formulaComponentType === node.type
    )

    return formulaFunction?.fromNodeToFormula(node)
  }
}
