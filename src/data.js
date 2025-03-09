const fs = require('fs');
const path = require('path');

const dataFile = path.join(__dirname, 'data', 'data.json');
let data = { users: {}, zones: {} };
let lastModified = 0; // Track the last modified time of the file

function loadData() {
  try {
    if (fs.existsSync(dataFile)) {
      const stats = fs.statSync(dataFile);
      const mtimeMs = stats.mtimeMs; // Last modified time in milliseconds
      if (mtimeMs > lastModified) { // Only reload if file has changed
        const fileContent = fs.readFileSync(dataFile, 'utf8');
        data = JSON.parse(fileContent);
        lastModified = mtimeMs;
        console.log(`Reloaded data.json at ${new Date().toISOString()}`);
      }
    } else {
      // Initialize with default zones if file doesn't exist
      data.zones = {
        'cinthria': '5 guards, 3 chests available',
        'cinthria-wilds': '9 dogs, 4 bandits left',
        'swamps': '7 crocodiles, 2 relics remaining',
        'the-shattered-crypt': '10 skeletons, 1 cursed artifact',
      };
      saveData();
      lastModified = fs.statSync(dataFile).mtimeMs;
      console.log(`Initialized ${dataFile} with default zones.`);
    }
  } catch (error) {
    console.error('Failed to load data.json:', error);
    // Don't overwrite in-memory data on error; keep existing state
  }
  return data;
}

function saveData() {
  try {
    fs.writeFileSync(dataFile, JSON.stringify(data, null, 2), 'utf8');
    lastModified = fs.statSync(dataFile).mtimeMs;
  } catch (error) {
    console.error('Failed to save data to data.json:', error);
  }
}

function getData() {
  return data; // Return the current in-memory data
}

// Initial load
loadData();

// Check for external updates every 60 seconds
setInterval(() => {
  loadData();
}, 20 * 1000); // 20 seconds

module.exports = { getData, saveData };