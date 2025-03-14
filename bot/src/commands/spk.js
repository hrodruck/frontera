// spk.js
require('dotenv').config();
const { processInput, getPlayerProgress } = require('../serverConnection');

const SESSION_ID = process.env.SESSION_ID;

let isPolling = false; // Flag to track if polling is active

async function handleSpk(message, args) {
  try {
    const USER_ID = message.author.id;
    const playerInput = args.join(' '); // e.g., "Look around"
    if (!playerInput) {
      await message.reply('Please provide an action after !spk (e.g., !spk Look around)');
      return;
    }

    // Process the player's input and send immediate response
    const inputResponse = await processInput(SESSION_ID, USER_ID, playerInput);
    const replyMessage = inputResponse || "No response from the game.";
    await message.reply(replyMessage);

    // Start asynchronous polling for player progress
    if (inputResponse !== "You already have a command waiting!"){
        
        const pollProgress = async () => {
          /*if (isPolling) {
            console.log('Polling already in progress, skipping new poll request.');
            return; // Exit if polling is already active
          }*/

          isPolling = true; // Set flag to indicate polling has started
          const interval = setInterval(async () => {
            try {
              const playerProgress = await getPlayerProgress(SESSION_ID, USER_ID);
              if (playerProgress && playerProgress.trim() !== '') {
                await message.reply(`Progress: ${playerProgress}`);
                clearInterval(interval);
                isPolling = false; // Reset flag when polling stops
              }
            } catch (error) {
              console.error('Error polling player progress:', error);
              await message.reply('Error checking progress!');
              clearInterval(interval);
              isPolling = false; // Reset flag on error
            }
          }, 1000); // Poll every 1 second
        };

// Start polling
pollProgress();
    }
  } catch (error) {
    console.error('Error handling !spk command:', error);
    await message.reply('Something went wrong with !spk!');
  }
}

module.exports = { handleSpk };