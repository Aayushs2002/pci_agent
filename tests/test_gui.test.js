import { render, screen } from '@testing-library/react';
import App from '../src/App';

// Mock electronAPI
global.window.electronAPI = {
  getSettings: jest.fn().mockResolvedValue({}),
  saveSettings: jest.fn().mockResolvedValue({ success: true }),
  onScanOutput: jest.fn(),
  onScanProgress: jest.fn(),
  onScanComplete: jest.fn(),
  onScanError: jest.fn(),
  removeAllListeners: jest.fn()
};

test('renders PCI Compliance Agent', () => {
  render(<App />);
  const linkElement = screen.getByText(/PCI Compliance Agent/i);
  expect(linkElement).toBeInTheDocument();
});

test('renders dashboard by default', () => {
  render(<App />);
  const dashboardElement = screen.getByText(/Dashboard/i);
  expect(dashboardElement).toBeInTheDocument();
});