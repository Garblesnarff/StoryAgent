import React from 'react';
import './styles/globals.css';
import { 
  createBrowserRouter, 
  RouterProvider,
  createRoutesFromElements,
  Route
} from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import StoryGeneration from './pages/StoryGeneration';
import BookUpload from './pages/BookUpload';
import NodeEditor from './components/NodeEditor';

const routes = [
  {
    element: <Layout />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/create-story", element: <StoryGeneration /> },
      { path: "/upload-book", element: <BookUpload /> },
      { path: "/story/edit", element: <NodeEditor /> }
    ]
  }
];

const router = createBrowserRouter(routes);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
