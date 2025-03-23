// playerState.js
require('dotenv').config(); // To access SESSION_ID
const { getPlayerProgress } = require('./serverConnection');
const { getData, saveData } = require('./data');

const pollingStates = new Map(); // In-memory polling state, cleared on restart
let loginLock = false; // Simple lock for login state changes

function isPlayerLoggedIn(userId) {
  const data = getData();
  return data.users[userId]?.isLoggedIn || false;
}

function setPlayerLoggedIn(userId, threadId, zone, subzone) {
  if (loginLock) return false; // Prevent changes if locked
  loginLock = true;
  const data = getData();
  if (!data.users[userId]) {
    data.users[userId] = { zones: {}, allowedZones: [], allowedSubzones: {} };
  }
  data.users[userId].isLoggedIn = true;
  data.users[userId].currentThreadId = threadId;
  data.users[userId].currentZone = { zone, subzone };
  saveData(data);
  loginLock = false;
  return true;
}

function setPlayerLoggedOut(userId) {
  if (loginLock) return false;
  loginLock = true;
  const data = getData();
  if (data.users[userId]?.isLoggedIn) {
    data.users[userId].isLoggedIn = false;
    data.users[userId].currentThreadId = null;
    if (data.users[userId].zones?.[data.users[userId].currentZone.zone]) {
      data.users[userId].zones[data.users[userId].currentZone.zone].hasSeenMessage = false;
      data.users[userId].zones[data.users[userId].currentZone.zone].subzones[
        data.users[userId].currentZone.subzone
      ].hasSeenMessage = false;
    }
    saveData(data);
    stopPolling(userId); // Stop polling on logout
  }
  loginLock = false;
  return true;
}

function startPolling(userId, thread) {
  if (pollingStates.has(userId)) return; // Already polling
  let lastActivity = Date.now();
  const interval = setInterval(async () => {
    try {
      const data = getData();
      if (!data.users[userId]?.isLoggedIn) {
        clearInterval(interval);
        pollingStates.delete(userId);
        return;
      }
      if (Date.now() - lastActivity > 10 * 60 * 1000) { // 10-minute AFK timer
        clearInterval(interval);
        pollingStates.delete(userId);
        await thread.send("Polling stopped due to inactivity.");
        return;
      }
      const playerProgress = await getPlayerProgress(process.env.SESSION_ID, userId);
      if (playerProgress && playerProgress.trim() !== '') {
        await thread.send(`Progress: ${playerProgress}`);
      }
    } catch (error) {
      console.error(`Error polling for ${userId}:`, error);
      clearInterval(interval);
      pollingStates.delete(userId);
    }
  }, 1000);
  pollingStates.set(userId, { interval, lastActivity });
}

function stopPolling(userId) {
  const state = pollingStates.get(userId);
  if (state) {
    clearInterval(state.interval);
    pollingStates.delete(userId);
  }
}

function updateLastActivity(userId, thread) {
  if (pollingStates.has(userId)){
      const state = pollingStates.get(userId);
      if (state) {
        state.lastActivity = Date.now();
      }
  }
  startPolling(userId, thread) //if it's already polling, startpolling will ignore this line
  
}

module.exports = {
  isPlayerLoggedIn,
  setPlayerLoggedIn,
  setPlayerLoggedOut,
  startPolling,
  stopPolling,
  updateLastActivity,
};