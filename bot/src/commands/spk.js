// spk.js
require('dotenv').config();
const { processInput, getPlayerProgress } = require('../serverConnection');

const SESSION_ID = process.env.SESSION_ID;

// Object to track polling state per user ID
const pollingStates = new Map(); // Using Map for better performance with dynamic keys

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
    if (inputResponse !== "You already have a command waiting!") {
      const pollProgress = async () => {
        // Check if this user is already polling
        if (pollingStates.get(USER_ID)) {
          console.log(`Polling already in progress for user ${USER_ID}, skipping new poll request.`);
          return; // Exit if polling is already active for this user
        }

        pollingStates.set(USER_ID, true); // Set flag to indicate polling has started for this user
        const interval = setInterval(async () => {
          try {
            const playerProgress = await getPlayerProgress(SESSION_ID, USER_ID);
            
            if (playerProgress && playerProgress.trim() !== '') {
              await message.reply(`Progress: ${playerProgress}`);
              // Uncomment these lines if you want to stop polling after progress is received
              // clearInterval(interval);
              // pollingStates.set(USER_ID, false);
            }
          } catch (error) {
            console.error(`Error polling player progress for user ${USER_ID}:`, error);
            await message.reply('Error checking progress!');
            clearInterval(interval);
            pollingStates.set(USER_ID, false); // Reset flag on error
          }
        }, 1000); // Poll every 1 second
      };

      // Start polling if not already polling for this user
      if (!pollingStates.get(USER_ID)) {
        pollProgress();
      }
    }
  } catch (error) {
    console.error('Error handling !spk command:', error);
    await message.reply('Something went wrong with !spk!');
  }
}

module.exports = { handleSpk };