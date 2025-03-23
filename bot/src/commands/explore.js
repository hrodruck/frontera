require('dotenv').config();
const { getData, saveData, initializeUser } = require('../data');
const { startGame } = require('../serverConnection');
const { setPlayerLoggedIn, isPlayerLoggedIn, startPolling } = require('../playerState');

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
      saveData(data);
    }

    const userData = data.users[user.id];
    await startGame(`${SESSION_ID}`, user.id, {}); // No room data needed

    const zoneChannel = message.guild.channels.cache.find(ch => ch.name === 'frontera' && ch.type === 0)
      || await message.guild.channels.create({ name: 'frontera', type: 0, parent: message.guild.channels.cache.find(ch => ch.name === 'Frontera' && ch.type === 4) });

    await zoneChannel.threads.fetchActive();
    const threadName = `explore-${user.username}`;
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
      await thread.send(`${user}, welcome to your adventure! The game server will guide you.`);
    } else {
      await thread.send(`${user}, welcome back...`);
    }

    setPlayerLoggedIn(user.id, thread.id);
    startPolling(user.id, thread);
  } catch (error) {
    console.error(`Error in handleExplore for ${user.tag}:`, error);
    await message.reply('Something went wrong while logging in. Try again later!');
  }
}

module.exports = { handleExplore };