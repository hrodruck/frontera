const { processInput } = require('../serverConnection');
const { isPlayerLoggedIn, updateLastActivity } = require('../playerState');

async function handleLook(message) {
  const userId = message.author.id;
  if (!isPlayerLoggedIn(userId)) {
    await message.reply("You need to log in with !explore first!");
    return;
  }

  try {
    const command = "!look";
    const response = await processInput(process.env.SESSION_ID, userId, command);
    await message.reply(response || "No response from the game.");
    updateLastActivity(userId, message.channel); // Reset AFK timer
  } catch (error) {
    console.error('Error handling !look command:', error);
    await message.reply('Something went wrong with !look!');
  }
}

module.exports = { handleLook };