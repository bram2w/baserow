export class Observer {
  constructor() {
    this.clear()
  }

  clear() {
    this.events = []
  }

  fire(...args) {
    for (const event in this.events) {
      this.events[event](...args)
    }
  }

  register(event) {
    this.events.push(event)
  }
}
