export class FromTipTapVisitor {
  constructor(functions) {
    this.functions = functions
  }

  visit(node) {
    switch (node.type) {
      case 'text':
        return this.visitText(node)
      case 'doc':
        return this.visitDoc(node)
      case 'wrapper':
        return this.visitWrapper(node)
      default:
        return this.visitFunction(node)
    }
  }

  visitDoc(node) {
    if (!node.content || node.content.length === 0) {
      return ''
    }

    const nodeContents = node.content.map(this.visit.bind(this))

    if (nodeContents.length === 1) {
      if (nodeContents[0] === "''") {
        return ''
      } else {
        return nodeContents[0]
      }
    }

    // Add the newlines between root wrappers. They are paragraphs.
    return `concat(${nodeContents.join(", '\n', ")})`
  }

  visitWrapper(node) {
    if (!node.content || node.content.length === 0) {
      // An empty wrapper is an empty string
      return "''"
    }

    if (node.content.length === 1) {
      return this.visit(node.content[0])
    }

    return `concat(${node.content.map(this.visit.bind(this)).join(', ')})`
  }

  visitText(node) {
    return `'${node.text.replace(/'/g, "\\'")}'`
  }

  visitFunction(node) {
    const formulaFunction = Object.values(this.functions.getAll()).find(
      (functionCurrent) => functionCurrent.formulaComponentType === node.type
    )

    return formulaFunction?.fromNodeToFormula(node)
  }
}
