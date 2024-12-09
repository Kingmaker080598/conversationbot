// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import { Box } from '@mui/material';

export default function App() {
  return (
    <Router>
      {/* Center-align content using Material-UI Box */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          padding: '20px',
        }}
      >
        <Routes>
          <Route path="/" element={<LandingPage />} />
        </Routes>
      </Box>
    </Router>
  );
}
