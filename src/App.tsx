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
import AnimatedTransition from './components/AnimatedTransition';

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={<Layout />}>
      <Route path="/" element={
        <AnimatedTransition>
          <LandingPage />
        </AnimatedTransition>
      } />
      <Route path="/create-story" element={
        <AnimatedTransition>
          <StoryGeneration />
        </AnimatedTransition>
      } />
      <Route path="/upload-book" element={
        <AnimatedTransition>
          <BookUpload />
        </AnimatedTransition>
      } />
      <Route path="/story/edit" element={
        <AnimatedTransition>
          <NodeEditor />
        </AnimatedTransition>
      } />
    </Route>
  ),
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
      v7_fetcherPersist: true,
      v7_normalizeFormMethod: true,
      v7_partialHydration: true,
      v7_skipActionErrorRevalidation: true,
    }
  }
);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
