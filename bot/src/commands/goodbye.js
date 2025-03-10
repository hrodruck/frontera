const { getData, saveData } = require('../data');

async function handleGoodbye(message) {
  const user = message.author;
  const data = getData();

  if (!data.users[user.id] || !data.users[user.id].currentZone.zone || !data.users[user.id].isLoggedIn) {
    await message.reply("You’re not currently logged into any zone!");
    return;
  }

  const zone = data.users[user.id].currentZone.zone;
  const subzone = data.users[user.id].currentZone.subzone;
  const zoneChannel = message.guild.channels.cache.find(ch => ch.name === zone && ch.type === 0);

  try {
    // Reset hasSeenMessage for the current zone
    if (data.users[user.id].zones?.[zone]) {
      data.users[user.id].zones[zone].hasSeenMessage = false;
      data.users[user.id].zones[zone].subzones[subzone].hasSeenMessage = false;
    }

    if (zoneChannel) {
      await zoneChannel.threads.fetchActive();
      const threadName = `${zone}-${user.username}`;
      const thread = zoneChannel.threads.cache.find(
        (thread) => thread.name === threadName && thread.archived === false
      );

      if (thread) {
        await thread.send(`${user}, you log off from ${zone}. Goodbye!`);
        await thread.members.remove(user.id);
        await thread.delete(); // Changed from setArchived(true) to delete()
      }
    }

    if (data.users[user.id].isLoggedIn) {
      data.users[user.id].isLoggedIn = false;
      saveData(data); // Updated to pass data parameter
    }
  } catch (error) {
    console.error(`Error in handleGoodbye for ${user.tag}:`, error);
    await message.reply('Something went wrong while logging off. Try again later!');
  }
}

module.exports = { handleGoodbye };