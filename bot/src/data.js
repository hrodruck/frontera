const fs = require('fs');
const path = require('path');

let data = { users: {}, zones: {} };
let lastModified = 0;

function loadData(filePath = path.join(__dirname, 'data', 'data.json')) {
  try {
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      if (stats.mtimeMs > lastModified) {
        data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        lastModified = stats.mtimeMs;
      }
    } else {
      data.zones = {
        'cinthria': {
          description: 'Welcome to the town of Cinthria!',
          subzones: {
            'prison-vault': 'An unwelcoming place',
            'town-hall': 'For all official matters',
            'temple-in-cinthria': 'A sacred temple with ancient carvings on the walls.',
            'market-square': '(not-implemented) A bustling market filled with merchants.'
          }
        }
      };
      data.defaultZone = 'cinthria';
      data.defaultSubzone = 'prison-vault'; // Add defaultSubzone at the same level as defaultZone
      saveData(data); // Pass data explicitly
      lastModified = fs.statSync(filePath).mtimeMs;
    }
  } catch (error) {
    console.error(`Failed to load ${filePath}:`, error);
  }
  return data;
}

function saveData(dataToSave = data, filePath = path.join(__dirname, 'data', 'data.json')) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(dataToSave, null, 2), 'utf8');
    lastModified = fs.statSync(filePath).mtimeMs;
  } catch (error) {
    console.error(`Failed to save ${filePath}:`, error);
  }
}

function getData() {
  return data;
}

// New function to initialize a user
function initializeUser(userId) {
  if (!data.users[userId]) {
    data.users[userId] = {
      zones: {},
      currentZone: { 
        zone: data.defaultZone, 
        subzone: data.defaultSubzone // Use defaultSubzone from data
      },
      isLoggedIn: false,
      allowedZones: [data.defaultZone], // Default to starting zone
      allowedSubzones: { [data.defaultZone]: [data.defaultSubzone] } // Initialize with defaultSubzone
    };
    saveData();
  }
  return data.users[userId];
}

// Initial load
loadData();

module.exports = { getData, saveData, loadData, initializeUser };