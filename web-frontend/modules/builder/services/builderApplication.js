const fakeApplicationData = [
  {
    hostname: 'test1.getbaserow.io',
    pages: [
      { path: '/', content: 'Site 1 page 1' },
      { path: '/test/', content: 'Site 1 page 2' },
      { path: '/test/:id', content: 'Site 1 page 3' },
      { path: '/foo/:id', content: 'Site 1 page 4' },
    ],
  },
  {
    hostname: 'test2.getbaserow.io',
    pages: [
      { path: '/', content: 'Site 2 page 1' },
      { path: '/foo/:id', content: 'Site 2 page 2' },
    ],
  },
]

// Fake service
export default (client) => {
  return {
    fetchByHostname(hostname) {
      return new Promise((resolve, reject) => {
        for (const app of fakeApplicationData) {
          if (app.hostname === hostname) {
            return resolve(app)
          }
        }
        reject(new Error('Application not found.'))
      })
    },
    fetchById(appId) {
      return new Promise((resolve, reject) => {
        if (Object.prototype.hasOwnProperty.call(fakeApplicationData, appId)) {
          resolve(fakeApplicationData[appId])
        } else {
          reject(new Error('Application not found.'))
        }
      })
    },
  }
}
