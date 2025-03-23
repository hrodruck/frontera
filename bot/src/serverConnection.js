require('dotenv').config();
const axios = require('axios');
const seedrandom = require('seedrandom');

const SERVER_URL = process.env.SERVER_URL;
const RANDOM_SEED = process.env.RANDOM_SEED


function getMappedPlayerId(originalPlayerId) {
  const rng = seedrandom(RANDOM_SEED + originalPlayerId);
  
  const min = 10000000;
  const max = 99999999;
  const mappedId = Math.floor(rng() * (max - min + 1)) + min;
  
  return `${mappedId}`;
}

async function startGame(sessionId, playerId) {
  try {
    const response = await axios.post(`${SERVER_URL}/api/start-game`, {
      session_id: `${sessionId}-${playerId}`,
      player_id: getMappedPlayerId(playerId)
    });
    console.log('Game started:', response.data.message);
    return response.data;
  } catch (error) {
    console.error('Error starting game:', error.response ? error.response.data : error.message);
    throw error;
  }
}

async function processInput(sessionId, playerId, command) {
  try {
    const response = await axios.post(`${SERVER_URL}/api/process-input`, {
      command,
      session_id: `${sessionId}-${playerId}`,
      player_id: getMappedPlayerId(playerId)
    });
    return response.data.response;
  } catch (error) {
    console.error('Error processing input:', error.response ? error.response.data : error.message);
    throw error;
  }
}

async function getPlayerProgress(sessionId, playerId) {
  try {
    const response = await axios.post(`${SERVER_URL}/api/player-progress`, {
      session_id: `${sessionId}-${playerId}`,
      player_id: getMappedPlayerId(playerId)
    });
    return response.data.response;
  } catch (error) {
    console.error('Error getting player progress:', error.response ? error.response.data : error.message);
    throw error;
  }
}

module.exports = { startGame, processInput, getPlayerProgress };
