// data.js
const fs = require('fs');
const path = require('path');

let userData = { users: {} };
let zoneData = { zones: {}, defaultZone: 'cinthria', defaultSubzone: 'prison-vault' };
let lastModifiedUsers = 0;
let lastModifiedZones = 0;

function loadData(
  usersFilePath = path.join(__dirname, 'data', 'users.json'),
  zonesFilePath = path.join(__dirname, 'data', 'zones.json')
) {
  try {
    // Load users.json
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

    // Load zones.json
    if (fs.existsSync(zonesFilePath)) {
      const stats = fs.statSync(zonesFilePath);
      if (stats.mtimeMs > lastModifiedZones) {
        zoneData = JSON.parse(fs.readFileSync(zonesFilePath, 'utf8'));
        lastModifiedZones = stats.mtimeMs;
      }
    } else {
      zoneData = {
        zones: {
          'cinthria': {
            description: 'Welcome to the town of Cinthria!',
            subzones: {
              'prison-vault': {
                short_description: 'An unwelcoming place',
                long_description: 'This is a place to store prisoners in the city of Cinthria. You have no idea why you\'re here. Maybe there\'s a way to get out...',
                room: {
                  description: {
                    door: 'Okay, there is a door in this room. It is large, made of old wood, and imposing. There is a keyhole in the door. The door is not magical. Make the keyhole inconspicuous. The door is locked. The door unlocks if the player inserts key_001 into the keyhole.',
                    doormat: 'Next to the door there\'s a doormat. Under the doormat is a concealed key. The doormat is flammable.',
                    torch: 'This torch is the only light source in the room. It can be moved from its place by the player. It can also be snuffed and put out by the player, though it has plenty of fuel and burns brightly.',
                    player_body: 'The player\'s own body, full of physical characteristics. The player is a regular, able adventurer. Keep track of things concerning the player body only, not other surrounding objects or features. Always reply in first person, from the perspective of a game avatar.',
                    inventory: 'The player set of possessions. It is initially empty',
                    key_001: 'This is a key under the doormat. The key is hidden from the player. This is key_001',
                    win_condition: 'An abstract entity to represent the win condition "the door is open". The player wins when they open the door or otherwise leave the room. This abstract object states whether that happened or not.',
                    room_itself: 'The description of the room itself based on all we\'ve discussed'
                  },
                  winning_message: "Congratulations! You've escaped the room!",
                  losing_message: "",
                }
              },
              'town-hall': 'For all official matters',
              'temple-in-cinthria': 'A sacred temple with ancient carvings on the walls.',
              'market-square': '(not-implemented) A bustling market filled with merchants.'
            }
          }
        },
        defaultZone: 'cinthria',
        defaultSubzone: 'prison-vault'
      };
      saveData(zoneData, zonesFilePath, 'zones');
      lastModifiedZones = fs.statSync(zonesFilePath).mtimeMs;
    }
  } catch (error) {
    console.error('Failed to load data:', error);
  }
  return getData();
}

function saveData(
  dataToSave,
  filePath = path.join(__dirname, 'data', 'data.json'), // Default for backward compatibility
  type = null // 'users' or 'zones' to specify which file to save
) {
  try {
    if (type === 'users') {
      fs.writeFileSync(filePath, JSON.stringify(dataToSave, null, 2), 'utf8');
      lastModifiedUsers = fs.statSync(filePath).mtimeMs;
    } else if (type === 'zones') {
      fs.writeFileSync(filePath, JSON.stringify(dataToSave, null, 2), 'utf8');
      lastModifiedZones = fs.statSync(filePath).mtimeMs;
    } else {
      fs.writeFileSync(
        path.join(__dirname, 'data', 'users.json'),
        JSON.stringify(userData, null, 2),
        'utf8'
      );
      fs.writeFileSync(
        path.join(__dirname, 'data', 'zones.json'),
        JSON.stringify(zoneData, null, 2),
        'utf8'
      );
      lastModifiedUsers = fs.statSync(path.join(__dirname, 'data', 'users.json')).mtimeMs;
      lastModifiedZones = fs.statSync(path.join(__dirname, 'data', 'zones.json')).mtimeMs;
    }
  } catch (error) {
    console.error(`Failed to save ${filePath}:`, error);
  }
}

function getData() {
  return {
    users: userData.users,
    zones: zoneData.zones,
    defaultZone: zoneData.defaultZone,
    defaultSubzone: zoneData.defaultSubzone
  };
}

function initializeUser(userId) {
  if (!userData.users[userId]) {
    userData.users[userId] = {
      zones: {},
      currentZone: { 
        zone: zoneData.defaultZone, 
        subzone: zoneData.defaultSubzone
      },
      isLoggedIn: false,
      allowedZones: [zoneData.defaultZone],
      allowedSubzones: { [zoneData.defaultZone]: [zoneData.defaultSubzone] }
    };
    saveData(userData, path.join(__dirname, 'data', 'users.json'), 'users');
  }
  return userData.users[userId];
}

// Initial load
loadData();

module.exports = { getData, saveData, loadData, initializeUser };