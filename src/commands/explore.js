const { getData, saveData } = require('../data');
const { getZoneStatus, getDefaultSubzone } = require('./zoneUtils');

async function handleExplore(message) {
  const channel = message.channel;
  const user = message.author;
  const data = getData();

  if (channel.type !== 0) {
    await message.reply("This command only works in text channels!");
    return;
  }

  try {
    // Initialize user data if it doesn't exist
    if (!data.users[user.id]) {
      if (!data.defaultZone) throw new Error("Default zone not found");
      const defaultSubzone = getDefaultSubzone(data.defaultZone);
      data.users[user.id] = {
        zones: {
          [data.defaultZone]: {
            hasSeenMessage: false,
            subzones: {
              [defaultSubzone]: { hasSeenMessage: false }
            }
          }
        },
        currentZone: { zone: data.defaultZone, subzone: defaultSubzone },
        isLoggedIn: false
      };
      saveData();
    }

    const userData = data.users[user.id];
    const currentLocation = userData.currentZone;
    const zone = currentLocation.zone;

    // Check if the zone channel exists
    const zoneChannel = message.guild.channels.cache.find(ch => ch.name === zone && ch.type === 0);
    if (!zoneChannel) {
      await message.reply(`Error: Your current zone (${zone}) no longer exists! Resetting to default.`);
      const defaultSubzone = getDefaultSubzone(data.defaultZone);
      userData.currentZone = { zone: data.defaultZone, subzone: defaultSubzone };
      // Initialize zone data if not present
      if (!userData.zones[data.defaultZone]) {
        userData.zones[data.defaultZone] = { hasSeenMessage: false, subzones: {} };
      }
      if (!userData.zones[data.defaultZone].subzones[defaultSubzone]) {
        userData.zones[data.defaultZone].subzones[defaultSubzone] = { hasSeenMessage: false };
      }
      saveData();
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

    // Construct the location string for display
    const locationString = currentLocation.subzone
      ? `${zone} (${currentLocation.subzone})`
      : zone;

    if (!userData.isLoggedIn) {
      const zoneStatus = getZoneStatus(zone, currentLocation.subzone);
      await thread.send(
        `${user}, welcome to your adventure in ${locationString}!\n**Zone Status**:\n${zoneStatus}`
      );
      // Set hasSeenMessage to true for zone and subzone
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
      saveData();
    } else {
      await thread.send(`${user}, you log into ${locationString}...`);
    }
  } catch (error) {
    console.error(`Error in handleExplore for ${user.tag}:`, error);
    await message.reply('Something went wrong while logging in. Try again later!');
  }
}

module.exports = { handleExplore };