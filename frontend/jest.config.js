const createJestConfig = require('next/jest')({
  dir: './',
})

/** @type {import('jest').Config} */
const customConfig = {
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
}

module.exports = createJestConfig(customConfig)
