import { createBrowserRouter } from 'react-router';
import { Layout } from './components/layout';
import { SessionsPage } from './pages/sessions';
import { NetworkPage } from './pages/network';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Layout,
    children: [
      {
        index: true,
        Component: SessionsPage,
      },
      {
        path: 'network',
        Component: NetworkPage,
      },
    ],
  },
]);
