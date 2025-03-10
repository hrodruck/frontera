// serverConnection.js
require('dotenv').config();
const axios = require('axios');

const SERVER_URL = process.env.SERVER_URL;

async function startGame(sessionId, roomData) {
  try {
    const response = await axios.post(`${SERVER_URL}/api/start-game`, {
      ...roomData,
      session_id: sessionId, // Override session_id with the provided value
    });
    console.log('Game started:', response.data.message);
    return response.data;
  } catch (error) {
    console.error('Error starting game:', error.response ? error.response.data : error.message);
    throw error;
  }
}

async function processInput(sessionId, command) {
  try {
    const response = await axios.post(`${SERVER_URL}/api/process-input`, {
      command,
      session_id: sessionId,
    });
    return response.data.response;
  } catch (error) {
    console.error('Error processing input:', error.response ? error.response.data : error.message);
    throw error;
  }
}

module.exports = { startGame, processInput };