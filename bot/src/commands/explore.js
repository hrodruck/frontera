// explore.js
require('dotenv').config();
const { getData, saveData, initializeUser } = require('../data');
const { getZoneStatus, getDefaultSubzone } = require('./zoneUtils');
const { startGame } = require('../serverConnection');
const { setPlayerLoggedIn, isPlayerLoggedIn, startPolling } = require('../playerState'); // Add startPolling
const path = require('path');

const SESSION_ID = process.env.SESSION_ID;

async function handleExplore(message, client) {
  const channel = message.channel;
  const user = message.author;
  const data = getData();

  if (channel.type !== 0) {
    await message.reply("This command only works in text channels! Not in threads!");
    return;
  }

  if (isPlayerLoggedIn(user.id)) {
    const thread = client.channels.cache.get(data.users[user.id].currentThreadId);
    if (thread && !thread.archived) {
      await message.reply(`You're already exploring! Head back to your thread: ${thread}`);
      return;
    }
  }

  try {
    if (!data.users[user.id]) {
      data.users[user.id] = initializeUser(user.id);
      data.users[user.id].zones = {
        [data.defaultZone]: {
          hasSeenMessage: false,
          subzones: { [data.defaultSubzone]: { hasSeenMessage: false } },
        },
      };
      saveData(data);
    }

    const userData = data.users[user.id];
    const currentLocation = userData.currentZone || { zone: data.defaultZone, subzone: data.defaultSubzone };
    const zone = currentLocation.zone;

    const roomData = data.zones[zone]?.subzones[currentLocation.subzone]?.room;
    if (!roomData) {
      await message.reply(`No room data found for ${currentLocation.subzone} in ${zone}!`);
      return;
    }

    await startGame(SESSION_ID, user.id, { room: roomData });

    const zoneChannel = message.guild.channels.cache.find(ch => ch.name === zone && ch.type === 0);
    if (!zoneChannel) {
      await message.reply(`Error: Your current zone (${zone}) no longer exists! Resetting to default.`);
      const defaultSubzone = getDefaultSubzone(data.defaultZone);
      userData.currentZone = { zone: data.defaultZone, subzone: defaultSubzone };
      userData.allowedZones = [data.defaultZone];
      userData.allowedSubzones = { [data.defaultZone]: [defaultSubzone] };
      if (!userData.zones[data.defaultZone]) {
        userData.zones[data.defaultZone] = { hasSeenMessage: false, subzones: {} };
      }
      if (!userData.zones[data.defaultZone].subzones[defaultSubzone]) {
        userData.zones[data.defaultZone].subzones[defaultSubzone] = { hasSeenMessage: false };
      }
      saveData(data);
      return;
    }

    await zoneChannel.threads.fetchActive();
    const threadName = `${zone}-${user.username}`;
    let thread = zoneChannel.threads.cache.find(t => t.name === threadName && !t.archived);

    if (!thread) {
      thread = await zoneChannel.threads.create({
        name: threadName,
        autoArchiveDuration: 60,
        type: 11,
        invitable: false,
      });
      await thread.members.add(user.id);
      await thread.members.add(client.user.id);
      console.log("Created thread:", thread.name);
    }

    if (!isPlayerLoggedIn(user.id)) {
      const locationString = currentLocation.subzone ? `${zone} (${currentLocation.subzone})` : zone;
      const zoneStatus = getZoneStatus(zone, currentLocation.subzone);
      await thread.send(`${user}, welcome to your adventure in ${locationString}!\n**Zone Status**:\n${zoneStatus}`);
      if (!userData.zones[zone]) {
        userData.zones[zone] = { hasSeenMessage: false, subzones: {} };
      }
      userData.zones[zone].hasSeenMessage = true;
      if (currentLocation.subzone) {
        if (!userData.zones[zone].subzones[currentLocation.subzone]) {
          userData.zones[zone].subzones[currentLocation.subzone] = { hasSeenMessage: false };
        }
        userData.zones[zone].subzones[currentLocation.subzone].hasSeenMessage = true;
      }
    } else {
      await thread.send(`${user}, welcome back to ${zone}...`);
    }

    setPlayerLoggedIn(user.id, thread.id, zone, currentLocation.subzone);
    startPolling(user.id, thread); // Start polling on login
  } catch (error) {
    console.error(`Error in handleExplore for ${user.tag}:`, error);
    await message.reply('Something went wrong while logging in. Try again later!');
  }
}

module.exports = { handleExplore };