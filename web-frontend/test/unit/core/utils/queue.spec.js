import { GroupTaskQueue } from '@baserow/modules/core/utils/queue'

function sleep(ms) {
  // FIXME: * 10 is a hack to increase the sleep time without the need to change all the
  // values. The problem is that timing is not always accurate when running tests in
  // parallel and this tests might fail because of that.
  return new Promise((resolve) => setTimeout(resolve, ms * 10))
}

// Split the test to make sure they run async. This actually helps with the sleep
// timing. Not super happy about these tests that rely on `sleep`, but I'm not aware
// of a better way of testing concurrency in this case.
describe('test GroupTaskQueue when immediately filling the queue', () => {
  test('test GroupTaskQueue when immediately filling the queue', async () => {
    let executed1 = false
    let executed2 = false

    const queue = new GroupTaskQueue()
    queue.add(async () => {
      await sleep(20)
      executed1 = true
    })
    queue.add(async () => {
      await sleep(20)
      executed2 = true
    })

    expect(executed1).toBe(false)
    expect(executed2).toBe(false)

    await sleep(15)

    expect(executed1).toBe(false)
    expect(executed2).toBe(false)

    await sleep(10)

    expect(executed1).toBe(true)
    expect(executed2).toBe(false)

    await sleep(20)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
  })
})
describe('test GroupTaskQueue adding to queue on the fly', () => {
  test('test GroupTaskQueue adding to queue on the fly', async () => {
    let executed1 = false
    let executed2 = false
    let executed3 = false

    const queue = new GroupTaskQueue()
    queue.add(async () => {
      await sleep(20)
      executed1 = true
    })

    expect(executed1).toBe(false)
    expect(executed2).toBe(false)
    expect(executed3).toBe(false)

    await sleep(15)

    expect(executed1).toBe(false)
    expect(executed2).toBe(false)
    expect(executed3).toBe(false)

    queue.add(async () => {
      await sleep(20)
      executed2 = true
    })

    await sleep(15)

    expect(executed1).toBe(true)
    expect(executed2).toBe(false)
    expect(executed3).toBe(false)

    queue.add(async () => {
      await sleep(20)
      executed3 = true
    })

    await sleep(15)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(false)

    await sleep(25)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(true)
  })
})
describe('test GroupTaskQueue with different ids', () => {
  test('test GroupTaskQueue with different ids', async () => {
    let executed1 = false
    let executed2 = false
    let executed3 = false

    const queue = new GroupTaskQueue()
    queue.add(async () => {
      await sleep(20)
      executed1 = true
    }, 1)

    await sleep(10)

    expect(executed1).toBe(false)
    expect(executed2).toBe(false)
    expect(executed3).toBe(false)

    queue.add(async () => {
      await sleep(20)
      executed2 = true
    }, 2)
    queue.add(async () => {
      await sleep(30)
      executed3 = true
    }, 1)

    await sleep(30)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(false)

    await sleep(10)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(true)
  })
})
describe('test GroupTaskQueue with waiting for add to resolve', () => {
  test('test GroupTaskQueue with waiting for add to resolve', async () => {
    let executed1 = false
    let executed2 = false
    let executed3 = false

    const queue = new GroupTaskQueue()
    queue
      .add(async () => {
        await sleep(20)
      })
      .then(() => {
        executed1 = true
      })
    queue
      .add(async () => {
        await sleep(20)
      })
      .then(() => {
        executed2 = true
      })
    queue
      .add(async () => {
        await sleep(20)
      })
      .then(() => {
        executed3 = true
      })

    await sleep(50)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(false)
  })
})
describe('test GroupTaskQueue with exception during execution', () => {
  test('test GroupTaskQueue with exception during execution', async () => {
    let failed1 = false
    let failed1Error = null
    let failed2 = false

    const queue = new GroupTaskQueue()
    queue
      .add(async () => {
        await sleep(20)
        throw new Error('test')
      })
      .then(() => {
        failed1 = false
      })
      .catch((error) => {
        failed1Error = error
        failed1 = true
      })
    queue
      .add(async () => {
        await sleep(20)
      })
      .then(() => {
        failed2 = false
      })
      .catch(() => {
        failed2 = true
      })

    await sleep(50)

    expect(failed1).toBe(true)
    expect(failed1Error.toString()).toBe('Error: test')
    expect(failed2).toBe(false)
  })
})
describe('test GroupTaskQueue with lock', () => {
  test('test GroupTaskQueue with exception during execution', async () => {
    let executed1 = false
    let executed2 = false
    let executed3 = false

    const queue = new GroupTaskQueue()
    queue.lock(1)
    queue.lock(2)

    queue.add(async () => {
      await sleep(20)
      executed1 = true
    }, 1)
    queue.add(async () => {
      await sleep(20)
      executed2 = true
    }, 2)
    queue.add(async () => {
      await sleep(20)
      executed3 = true
    }, 1)

    await sleep(30)

    expect(executed1).toBe(false)
    expect(executed2).toBe(false)
    expect(executed3).toBe(false)

    queue.release(2)

    await sleep(30)

    expect(executed1).toBe(false)
    expect(executed2).toBe(true)
    expect(executed3).toBe(false)

    queue.release(1)

    await sleep(30)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(false)

    await sleep(20)

    expect(executed1).toBe(true)
    expect(executed2).toBe(true)
    expect(executed3).toBe(true)
  })
})
describe('test queue deleted from GroupTaskQueue', () => {
  test('test queue deleted from GroupTaskQueue', async () => {
    const queue = new GroupTaskQueue()
    queue.add(async () => {
      await sleep(20)
    }, 1)

    expect(Object.prototype.hasOwnProperty.call(queue.queues, 1)).toBe(true)

    await sleep(30)

    expect(Object.prototype.hasOwnProperty.call(queue.queues, 1)).toBe(false)
  })
})
