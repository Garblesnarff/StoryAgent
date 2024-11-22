import React from 'react';
import './styles/globals.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import StoryGeneration from './pages/StoryGeneration';
import BookUpload from './pages/BookUpload';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/create-story" element={<StoryGeneration />} />
          <Route path="/upload-book" element={<BookUpload />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
