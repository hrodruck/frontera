// goodbye.js
const { getData } = require('../data');
const { setPlayerLoggedOut } = require('../playerState');

async function handleGoodbye(message) {
  const user = message.author;
  const data = getData();

  if (!data.users[user.id] || !data.users[user.id].isLoggedIn) {
    await message.reply("You’re not currently logged in!");
    return;
  }

  try {
    const threadId = data.users[user.id].currentThreadId;
    const thread = threadId ? message.client.channels.cache.get(threadId) : null;
    if (thread && !thread.archived) {
      await thread.send(`${user}, you log off. Goodbye!`);
      await thread.members.remove(user.id);
      await thread.delete(); // Normal case: delete the thread
    } else {
      // If thread not found in cache, just log out without error
      setPlayerLoggedOut(user.id); // Updates state and stops polling
      await message.reply("You’ve logged off successfully! (Thread not found, state cleared.)");
      return;
    }

    setPlayerLoggedOut(user.id); // Updates state and stops polling
  } catch (error) {
    console.error(`Error in handleGoodbye for ${user.tag}:`, error);
    const threadId = data.users[user.id].currentThreadId;
    const thread = threadId ? message.client.channels.cache.get(threadId) : null;
    if (thread !== null){
        await thread.delete();
    }
    setPlayerLoggedOut(user.id); // Ensure logout happens
  }
}

module.exports = { handleGoodbye };