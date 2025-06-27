import { render, screen } from '@testing-library/react';
import App from './App';
import { BrowserRouter } from 'react-router';

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe('App', () => {
  it('App renders expected text', () => {
    renderApp();
    expect(screen.getByText('Your reportable condition configurations')).toBeInTheDocument();
  });
});
