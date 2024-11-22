import React from 'react';
import './styles/globals.css';
import { 
  createBrowserRouter, 
  RouterProvider,
  Route,
  createRoutesFromElements
} from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import StoryGeneration from './pages/StoryGeneration';
import BookUpload from './pages/BookUpload';
import NodeEditor from './components/NodeEditor';

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={<Layout />}>
      <Route path="/" element={<LandingPage />} />
      <Route path="/create-story" element={<StoryGeneration />} />
      <Route path="/upload-book" element={<BookUpload />} />
      <Route path="/story/edit" element={<NodeEditor />} />
    </Route>
  ),
  {
    basename: '/'
  }
);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
