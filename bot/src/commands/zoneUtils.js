const { getData, saveData, initializeUser } = require('../data');

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
  const data = getData();
  // Return the default subzone from data if the zone matches the default zone, otherwise null
  return (zone === data.defaultZone) ? data.defaultSubzone : null;
}

function grantAccess(userId, zone, subzone = null) {
  const data = getData();
  let userData = data.users[userId];

  // Initialize user if they don’t exist
  if (!userData) {
    userData = initializeUser(userId);
  }

  // Ensure allowedZones and allowedSubzones exist
  userData.allowedZones = userData.allowedZones || [];
  userData.allowedSubzones = userData.allowedSubzones || {};

  // Grant access to the zone if not already allowed
  if (zone && !userData.allowedZones.includes(zone)) {
    userData.allowedZones.push(zone);
    // Initialize subzones array for the new zone if not present
    if (!userData.allowedSubzones[zone]) {
      userData.allowedSubzones[zone] = [];
    }
  }

  // Grant access to the subzone if specified and not already allowed
  if (subzone && zone && userData.allowedSubzones[zone] && !userData.allowedSubzones[zone].includes(subzone)) {
    userData.allowedSubzones[zone].push(subzone);
  }

  // Save the updated data
  saveData();
  return userData; // Return updated user data for convenience
}

module.exports = { getZoneStatus, getDefaultSubzone, grantAccess };