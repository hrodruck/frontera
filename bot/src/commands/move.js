const { processInput } = require('../serverConnection');
const { isPlayerLoggedIn, updateLastActivity } = require('../playerState');

async function handleMove(message, args) {
  const userId = message.author.id;
  if (!isPlayerLoggedIn(userId)) {
    await message.reply("You need to log in with !explore first!");
    return;
  }

  const subzone = args.join('-').toLowerCase();
  if (!subzone) {
    await message.reply("Please specify a subzone to move to! (e.g., !move prison-vault)");
    return;
  }

  try {
    const command = `!move ${subzone}`;
    const response = await processInput(process.env.SESSION_ID, userId, command);
    await message.reply(response || "No response from the game.");
    updateLastActivity(userId, message.channel); // Reset AFK timer
  } catch (error) {
    console.error('Error handling !move command:', error);
    await message.reply('Something went wrong with !move!');
  }
}

module.exports = { handleMove };