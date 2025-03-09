const { getData } = require('../data');

function getZoneStatus(zone, currentSubzone) {
  const data = getData();
  const zoneData = data.zones[zone];

  if (!zoneData) {
    return 'No status available yet.';
  }

  // Handle nested zone structure (with subzones)
  if (typeof zoneData === 'object' && zoneData.description) {
    let status = zoneData.description; // Start with the zone description
    if (currentSubzone && zoneData.subzones && zoneData.subzones[currentSubzone]) {
      status += `\n${currentSubzone}: ${zoneData.subzones[currentSubzone]}`; // Add only the current subzone
    }
    return status;
  }

  // Handle legacy string-based zones
  return zoneData;
}

function getDefaultSubzone(zone) {
  // Define default subzones for specific zones
  const defaultSubzones = {
    'cinthria': 'temple-in-cinthria'
  };
  return defaultSubzones[zone] || null;
}

module.exports = { getZoneStatus, getDefaultSubzone };