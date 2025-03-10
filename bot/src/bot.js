// bot.js
require('dotenv').config();
const { Client, IntentsBitField } = require('discord.js');
const { initializeZones } = require('./zones');
const { handleMessage } = require('./commands');

const client = new Client({
  intents: [
    IntentsBitField.Flags.Guilds,
    IntentsBitField.Flags.GuildMessages,
    IntentsBitField.Flags.MessageContent,
  ],
});

function startBot() {
  client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}`);
    initializeZones(client);
  });

  client.on('messageCreate', handleMessage);

  client.login(process.env.DISCORD_TOKEN);
}

module.exports = { startBot, client };