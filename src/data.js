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
        'cinthria': '5 guards, 3 chests available',
        'cinthria-wilds': '9 dogs, 4 bandits left',
        'swamps': '7 crocodiles, 2 relics remaining',
        'the-shattered-crypt': '10 skeletons, 1 cursed artifact',
      };
      saveData(filePath);
      lastModified = fs.statSync(filePath).mtimeMs;
    }
  } catch (error) {
    console.error(`Failed to load ${filePath}:`, error);
  }
  return data;
}

function saveData(dataToSave, filePath = path.join(__dirname, 'data', 'data.json')) {
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

// Initial load with default path
loadData();

module.exports = { getData, saveData, loadData };

