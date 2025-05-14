module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[jt]sx?$': 'babel-jest',
  },
  moduleFileExtensions: ['js', 'jsx', 'json', 'node'],
  transformIgnorePatterns: [
    '/node_modules/(?!(wavesurfer-react|wavesurfer.js)/)'
  ],
  setupFilesAfterEnv: ['<rootDir>/node_modules/@testing-library/jest-dom'],
  moduleNameMapper: {
    // Mock wavesurfer-react and wavesurfer.js for Jest (ESM compatibility workaround)
    '^wavesurfer-react$': '<rootDir>/src/__mocks__/wavesurfer-react.js',
    '^wavesurfer.js$': '<rootDir>/src/__mocks__/wavesurfer.js',
  },
  // Add ESM/JSX support for React and modern libraries
  extensionsToTreatAsEsm: ['.js', '.jsx'],
  testPathIgnorePatterns: ['/node_modules/', '/__pycache__/'],
  collectCoverageFrom: ['src/**/*.{js,jsx}', '!src/__mocks__/*'],
  verbose: true,
};
