const { getData, saveData, initializeUser } = require('../data');
const { getZoneStatus } = require('./zoneUtils');

async function handleMove(message, args) {
  const user = message.author;
  const data = getData();
  let userData = data.users[user.id];

  // Initialize user if they don’t exist
  if (!userData) {
    userData = initializeUser(user.id);
  }

  const currentZone = userData.currentZone.zone;
  const zoneData = data.zones[currentZone];

  // Check if the zone has subzones
  if (!zoneData || typeof zoneData !== 'object' || !zoneData.subzones) {
    await message.reply(`There are no subzones to move to in ${currentZone}!`);
    return;
  }

  // If no subzone is specified, list available subzones
  if (!args.length) {
    const availableSubzones = Object.keys(zoneData.subzones)
      .filter(subzone => userData.allowedSubzones[currentZone].includes(subzone))
      .join(', ');
    await message.reply(
      `Please specify a subzone to move to!\nAllowed subzones in ${currentZone}: ${availableSubzones}\nUse \`!move <subzone-name>\`.`
    );
    return;
  }

  const targetSubzone = args.join('-').toLowerCase();

  try {
    // Check if the target subzone exists
    if (!zoneData.subzones[targetSubzone]) {
      const availableSubzones = Object.keys(zoneData.subzones).join(', ');
      await message.reply(
        `Subzone "${targetSubzone}" not found in ${currentZone}. Available subzones: ${availableSubzones}`
      );
      return;
    }

    // Check if the subzone is allowed
    const allowedSubzones = userData.allowedSubzones[currentZone] || [];
    if (allowedSubzones.length > 0 && !allowedSubzones.includes(targetSubzone)) {
      await message.reply(`You are not allowed to move to "${targetSubzone}" in ${currentZone}!`);
      return;
    }

    // Prevent moving to the same subzone
    if (userData.currentZone.subzone === targetSubzone) {
      await message.reply(`You're already in ${targetSubzone}!`);
      return;
    }

    // Update the user's current subzone
    userData.currentZone.subzone = targetSubzone;
    saveData();

    // Send a confirmation message with the new subzone's status
    const zoneStatus = getZoneStatus(currentZone, targetSubzone);
    const locationString = `${currentZone} (${targetSubzone})`;
    await message.reply(
      `${user}, you move to ${locationString}.\n**Zone Status**:\n${zoneStatus}`
    );

  } catch (error) {
    console.error(`Error in handleMove for ${user.tag}:`, error);
    await message.reply('Something went wrong while moving. Try again later!');
  }
}

module.exports = { handleMove };

