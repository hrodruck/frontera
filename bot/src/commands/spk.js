// spk.js
require('dotenv').config();
const { processInput } = require('../serverConnection'); // Remove getPlayerProgress
const { isPlayerLoggedIn, updateLastActivity, startPolling } = require('../playerState'); // Remove startPolling

const SESSION_ID = process.env.SESSION_ID;

async function handleSpk(message, args) {
  const USER_ID = message.author.id;
  if (!isPlayerLoggedIn(USER_ID)) {
    await message.reply("You need to log in with !explore first!");
    return;
  }

  try {
    const playerInput = args.join(' ');
    if (!playerInput) {
      await message.reply('Please provide an action after !spk (e.g., !spk Look around)');
      return;
    }

    const inputResponse = await processInput(SESSION_ID, USER_ID, playerInput);
    const replyMessage = inputResponse || "No response from the game.";
    await message.reply(replyMessage);
    updateLastActivity(USER_ID, message.channel); // Reset AFK timer on input
    
  } catch (error) {
    console.error('Error handling !spk command:', error);
    await message.reply('Something went wrong with !spk!');
  }
}

module.exports = { handleSpk };