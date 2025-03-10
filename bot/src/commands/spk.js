// spk.js
require('dotenv').config();
const { processInput } = require('../serverConnection'); // Import processInput

async function handleSpk(message, args) {
  try {
    const SESSION_ID = message.author.id;
    const playerInput = args.join(' '); // e.g., "Look around"
    if (!playerInput) {
      await message.reply('Please provide an action after !spk (e.g., !spk Look around)');
      return;
    }

    const responseText = await processInput(SESSION_ID, playerInput);
    await message.reply(responseText || "No response from the game.");
  } catch (error) {
    console.error('Error handling !spk command:', error);
    await message.reply('Something went wrong with !spk!');
  }
}

module.exports = { handleSpk };