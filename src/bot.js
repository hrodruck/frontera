require('dotenv').config();
const { Client, IntentsBitField } = require('discord.js');
const { initializeZones } = require('./zones');
const { handleMessage } = require('./commands');
const axios = require('axios');

const SERVER_URL = process.env.SERVER_URL;

const client = new Client({
  intents: [
    IntentsBitField.Flags.Guilds,
    IntentsBitField.Flags.GuildMessages,
    IntentsBitField.Flags.MessageContent,
  ],
});

const roomData = {
  room: {
    description: {
      door: 'Okay, there is a door in this room. It is large, made of old wood, and imposing. There is a keyhole in the door. The door is not magical. Make the keyhole inconspicuous. The door is locked. The door unlocks if the player inserts key_001 into the keyhole.',
      doormat: 'Next to the door there\'s a doormat. Under the doormat is a concealed key. The doormat is flamable.',
      torch: 'This torch is the only light source in the room. It can be moved from it\'s place by the player. It can also be snuffed and put out by the player, though it is plenty of fuel and burns brightly.',
      player_body: 'The player\'s own body, full of physical characteristics. The player is a regular, able adventurer. Keep track of things concerning the player body only, not other surounding objects or features. Always reply in first person, from the perspective of a game avatar.',
      inventory: 'The player set of possessions. It is initially empty',
      key_001: 'This is a key under the doormat. The key is hidden from the player. This is key_001',
      win_condition: 'An abstract entity to represent the win condition "the door is open". The player wins when they open the door or otherwise leave the room. This abstract object states whether that happened or not.',
      room_itself: 'The description of the room itself based on all we\'ve discussed',
    },
    winning_message: "Congratulations! You've escaped the room!",
    losing_message: "",
    room_description: "The room is dimly lit, with a large, old wooden door dominating one wall. The door has a small, inconspicuous keyhole and appears to be locked. Next to the door is a doormat, and a single torch mounted on the wall provides the only light, casting a warm glow around the space. Your inventory is currently empty. There are no signs of any immediate threats, but the door is clearly the way out, and it needs to be unlocked to proceed.",
  },
  session_id: 'frontera',
};

async function startGame() {
  try {
    const response = await axios.post(`${SERVER_URL}/api/start-game`, roomData);
    console.log('Game started:', response.data.message);
  } catch (error) {
    console.error('Error starting game:', error.response ? error.response.data : error.message);
  }
}

function startBot() {
  client.once('ready', async () => {
    console.log(`Logged in as ${client.user.tag}`);
    await startGame(); // Start the game when the bot is ready
    initializeZones(client);
  });

  client.on('messageCreate', handleMessage);

  client.login(process.env.DISCORD_TOKEN);
}

module.exports = { startBot, client };

