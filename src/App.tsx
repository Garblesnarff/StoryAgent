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
import StoryEdit from './pages/StoryEdit';
import NodeEditor from './components/NodeEditor';

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={<Layout />}>
      <Route path="/" element={<LandingPage />} />
      <Route path="/create-story" element={<StoryGeneration />} />
      <Route path="/upload-book" element={<BookUpload />} />
      <Route path="/story/edit" element={<StoryEdit />} />
      <Route path="/story/edit/nodes" element={<NodeEditor />} />
    </Route>
  ),
  {
    future: {
      v7_relativeSplatPath: true,
      v7_fetcherPersist: true,
      v7_normalizeFormMethod: true,
      v7_partialHydration: true,
      v7_skipActionErrorRevalidation: true
    },
  }
);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
