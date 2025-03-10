require('dotenv').config();
const axios = require('axios');

const SERVER_URL = process.env.SERVER_URL;

async function handleSpk(message, args) {
  try {
    const SESSION_ID = message.author.id;
    const playerInput = args.join(' '); // e.g., "Look around"
    if (!playerInput) {
      await message.reply('Please provide an action after !spk (e.g., !spk Look around)');
      return;
    }

    // Send the input to the Python server
    const processResponse = await axios.post(`${SERVER_URL}/api/process-input`, {
      command: playerInput,
      session_id: SESSION_ID,
    });

    const responseText = `${processResponse.data.response}\n`.trim();
    await message.reply(responseText || "No response from the game.");
  } catch (error) {
    console.error('Error handling !spk command:', error);
    await message.reply('Something went wrong with !spk!');
  }
}

module.exports = { handleSpk };

