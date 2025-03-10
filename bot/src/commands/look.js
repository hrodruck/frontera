// In look.js
const { getData, saveData } = require('../data');

async function handleLook(message) {
  const data = getData();
  const userId = message.author.id;

  // Get user's current location
  const userData = data.users[userId] || {
    zones: {},
    currentZone: { zone: data.defaultZone, subzone: null },
    isLoggedIn: false
  };
  const currentLocation = userData.currentZone;
  const currentZone = currentLocation.zone;
  const currentSubzone = currentLocation.subzone;

  // Ensure zones object exists for the user
  if (!userData.zones[currentZone]) {
    userData.zones[currentZone] = { subzones: {} };
  }

  // Check if the user is in a valid zone
  if (!data.zones[currentZone]) {
    await message.reply("You're not in any zone!");
    return;
  }

  // Initialize flags and descriptions
  let zoneDescription = '';
  let subzoneDescription = '';
  let zoneHasSeen = userData.zones[currentZone]?.hasSeenMessage || false;
  let subzoneHasSeen = false;

  // Get zone description
  if (!zoneHasSeen) {
    zoneDescription = data.zones[currentZone].description || "This place seems empty...";
  }

  // Get subzone description if applicable
  if (currentSubzone && data.zones[currentZone].subzones && data.zones[currentZone].subzones[currentSubzone]) {
    subzoneHasSeen = userData.zones[currentZone].subzones[currentSubzone]?.hasSeenMessage || false;
    // Use long_description if available, otherwise fall back to short_description or existing behavior
    const subzoneData = data.zones[currentZone].subzones[currentSubzone];
    subzoneDescription = subzoneData.long_description || subzoneData.short_description || subzoneData;
  }

  // Combine descriptions or provide a default message
  let replyMessage = '';
  if (zoneDescription && subzoneDescription) {
    replyMessage = `${zoneDescription}\n${subzoneDescription}`;
  } else if (zoneDescription) {
    replyMessage = zoneDescription;
  } else if (subzoneDescription && !subzoneHasSeen) {
    replyMessage = subzoneDescription;
  } else {
    replyMessage = `Nothing new to see here. As a reminder, here you are:\n${currentZone} (${currentSubzone})\n${subzoneDescription}`;
  }

  // Reply with the combined message
  await message.reply(replyMessage);

  // Mark as seen if applicable
  let dataChanged = false;
  if (!zoneHasSeen) {
    userData.zones[currentZone] = {
      ...userData.zones[currentZone],
      hasSeenMessage: true
    };
    dataChanged = true;
  }
  if (currentSubzone && !subzoneHasSeen) {
    userData.zones[currentZone].subzones[currentSubzone] = {
      ...userData.zones[currentZone].subzones[currentSubzone],
      hasSeenMessage: true
    };
    dataChanged = true;
  }

  // Save data if anything changed
  if (dataChanged) {
    data.users[userId] = userData;
    saveData(data);
  }
}

module.exports = { handleLook };