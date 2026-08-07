export const FRONTEND_DEV_PORT = 5173

export const TEST_PORTS = Object.freeze({
  workbench: 5180,
  dashboard: 5181,
  tutorial: 5182,
})

export const testOrigin = (port) => `http://127.0.0.1:${port}`
