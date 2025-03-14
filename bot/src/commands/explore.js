// explore.js
require('dotenv').config();
const { getData, saveData, initializeUser } = require('../data');
const { getZoneStatus, getDefaultSubzone } = require('./zoneUtils');
const { startGame } = require('../serverConnection');
const path = require('path');

const SESSION_ID = process.env.SESSION_ID

async function handleExplore(message) {
  const channel = message.channel;
  const user = message.author;
  const data = getData();

  if (channel.type !== 0) {
    await message.reply("This command only works in text channels! Not in threads!");
    return;
  }

  try {
    if (!data.users[user.id]) {
      data.users[user.id] = initializeUser(user.id);
      data.users[user.id].zones = {
        [data.defaultZone]: {
          hasSeenMessage: false,
          subzones: {
            [data.defaultSubzone]: { hasSeenMessage: false }
          }
        }
      };
      saveData({'users':data.users}, path.join(__dirname, '../data/users.json'), 'users');
    }

    const userData = data.users[user.id];
    const currentLocation = userData.currentZone || { zone: data.defaultZone, subzone: data.defaultSubzone };
    const zone = currentLocation.zone;

    // Fetch room data from zones.json for the current subzone
    const roomData = data.zones[zone]?.subzones[currentLocation.subzone]?.room;
    if (!roomData) {
      await message.reply(`No room data found for ${currentLocation.subzone} in ${zone}!`);
      return;
    }

    // Start the game with the user's ID and room data
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
      saveData({'users':data.users}, path.join(__dirname, '../data/users.json'), 'users');
      return;
    }

    await zoneChannel.threads.fetchActive();
    const threadName = `${zone}-${user.username}`;
    const existingThread = zoneChannel.threads.cache.find(
      (thread) => thread.name === threadName && thread.archived === false
    );

    if (existingThread) {
      if (userData.isLoggedIn) {
        await existingThread.send(`${user}, you're already logged into ${zone}!`);
      } else {
        await existingThread.send(`${user}, you're not logged in! Please delete your existing exploring thread!`);
      }
      return;
    }

    const thread = await zoneChannel.threads.create({
      name: threadName,
      autoArchiveDuration: 60,
      type: 11,
      invitable: false,
    });

    await thread.members.add(user.id);
    await thread.members.add(message.client.user.id);
    console.log("Created thread:", thread.name);

    const locationString = currentLocation.subzone
      ? `${zone} (${currentLocation.subzone})`
      : zone;

    if (!userData.isLoggedIn) {
      const zoneStatus = getZoneStatus(zone, currentLocation.subzone);
      await thread.send(
        `${user}, welcome to your adventure in ${locationString}!\n**Zone Status**:\n${zoneStatus}`
      );
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
      userData.isLoggedIn = true;
      saveData({'users':data.users}, path.join(__dirname, '../data/users.json'), 'users');
    } else {
      await thread.send(`${user}, you log into ${locationString}...`);
    }
  } catch (error) {
    console.error(`Error in handleExplore for ${user.tag}:`, error);
    await message.reply('Something went wrong while logging in. Try again later!');
  }
}

module.exports = { handleExplore };