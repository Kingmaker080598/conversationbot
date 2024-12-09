import React, { useState } from 'react';
import { TextField, Button, Box, Container } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

export default function LandingPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState('');
  const [chatOpen, setChatOpen] = useState(false); // State to handle the chat box visibility
  const [chatMessages, setChatMessages] = useState([]); // State to hold chat messages

  // Function to handle fetching suggestions
  const getSuggestions = async () => {
    if (searchTerm.trim() === '') {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:5000/suggest?query=${searchTerm}`
      );

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []); // Adjust based on your API's response format
        setError('');
      } else {
        setError('Failed to fetch suggestions');
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to fetch suggestions');
    }
  };

  // Handle the 'Enter' key press to trigger the search
  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      getSuggestions();
    }
  };

  // Handle chat box toggling
  const handleChatToggle = () => {
    setChatOpen(!chatOpen);
  };

  // Handle sending messages to the chat API
  const sendMessage = async (message) => {
    const newMessage = { from: 'user', text: message };
    setChatMessages([...chatMessages, newMessage]);

    try {
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (response.ok) {
        const data = await response.json();
        const botMessage = { from: 'bot', text: data.response };
        setChatMessages([...chatMessages, newMessage, botMessage]);
      } else {
        setChatMessages([
          ...chatMessages,
          newMessage,
          { from: 'bot', text: 'Sorry, something went wrong!' },
        ]);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setChatMessages([
        ...chatMessages,
        newMessage,
        { from: 'bot', text: 'Failed to connect to the bot.' },
      ]);
    }
  };

  return (
    <Container
      maxWidth="sm"
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        position: 'relative',
      }}
    >
      <h1>Welcome to Retail Chatbot</h1>
      <p>Search for the best products or chat with our assistant!</p>

      {/* Search Bar Section */}
      <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: '50px' }}>
        <TextField
          label="Search for products"
          variant="outlined"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={handleKeyPress} // Trigger search on Enter key press
          sx={{ width: '300px', marginRight: '16px' }}
        />
        <Button
          variant="contained"
          onClick={getSuggestions}
          startIcon={<SearchIcon />}
          sx={{ height: '100%' }}
        >
          Search
        </Button>
      </Box>

      {/* Display Suggestions or Results */}
      <Box sx={{ marginTop: '20px' }}>
        <h3>Search Results</h3>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {suggestions.length === 0 && !error ? (
          <p>No results found. Try a different search.</p>
        ) : (
          <ul>
            {suggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        )}
      </Box>

      {/* Login Button at Top Right Corner */}
      <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
        <Button variant="contained" color="primary">
          Login
        </Button>
      </Box>

      {/* Chat Button at Bottom Right */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          right: 16,
        }}
      >
        <Button
          variant="contained"
          color="secondary"
          onClick={handleChatToggle}
        >
          {chatOpen ? 'Close Chat' : 'Chat with Bot'}
        </Button>
      </Box>

      {/* Chat Window */}
      {chatOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '80px',
            right: '16px',
            width: '300px',
            height: '400px',
            border: '1px solid #ccc',
            borderRadius: '8px',
            padding: '16px',
            backgroundColor: 'white',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div
            style={{
              height: '300px',
              overflowY: 'scroll',
              marginBottom: '10px',
              borderBottom: '1px solid #ccc',
            }}
          >
            {chatMessages.map((message, index) => (
              <div
                key={index}
                style={{
                  margin: '10px 0',
                  textAlign: message.from === 'user' ? 'right' : 'left',
                }}
              >
                <span
                  style={{
                    padding: '8px 12px',
                    borderRadius: '20px',
                    backgroundColor:
                      message.from === 'user' ? '#4caf50' : '#2196f3',
                    color: 'white',
                    display: 'inline-block',
                  }}
                >
                  {message.text}
                </span>
              </div>
            ))}
          </div>
          <TextField
            label="Type your message"
            variant="outlined"
            fullWidth
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.target.value.trim() !== '') {
                sendMessage(e.target.value);
                e.target.value = ''; // Clear input field
              }
            }}
          />
        </div>
      )}
    </Container>
  );
}
