const fs = require('fs');
const path = require('path');

let userData = { users: {} };
let lastModifiedUsers = 0;

function loadData(usersFilePath = path.join(__dirname, 'data', 'users.json')) {
  try {
    if (fs.existsSync(usersFilePath)) {
      const stats = fs.statSync(usersFilePath);
      if (stats.mtimeMs > lastModifiedUsers) {
        userData = JSON.parse(fs.readFileSync(usersFilePath, 'utf8'));
        lastModifiedUsers = stats.mtimeMs;
      }
    } else {
      userData = { users: {} };
      saveData(userData, usersFilePath, 'users');
      lastModifiedUsers = fs.statSync(usersFilePath).mtimeMs;
    }
  } catch (error) {
    console.error('Failed to load user data:', error);
  }
  return getData();
}

function saveData(dataToSave, filePath = path.join(__dirname, 'data', 'users.json'), type = 'users') {
  try {
    if (type === 'users') {
      fs.writeFileSync(filePath, JSON.stringify(dataToSave, null, 2), 'utf8');
      lastModifiedUsers = fs.statSync(filePath).mtimeMs;
    }
  } catch (error) {
    console.error(`Failed to save ${filePath}:`, error);
  }
}

function getData() {
  return { users: userData.users };
}

function initializeUser(userId) {
  if (!userData.users[userId]) {
    userData.users[userId] = {
      isLoggedIn: false,
      currentThreadId: null,
      currentZone: null, // No longer stores zone/subzone locally
    };
    saveData(userData, path.join(__dirname, 'data', 'users.json'), 'users');
  }
  return userData.users[userId];
}

// Initial load
loadData();

module.exports = { getData, saveData, loadData, initializeUser };