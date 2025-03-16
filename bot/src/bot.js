// bot.js
require('dotenv').config();
const { Client, IntentsBitField } = require('discord.js');
const { initializeZones } = require('./zones');
const { handleMessage } = require('./commands');
const { isPlayerLoggedIn, setPlayerLoggedIn } = require('./playerState');
const { getData } = require('./data');

const client = new Client({
  intents: [
    IntentsBitField.Flags.Guilds,
    IntentsBitField.Flags.GuildMessages,
    IntentsBitField.Flags.MessageContent,
  ],
});

async function startBot() {
  client.once('ready', async () => {
    console.log(`Logged in as ${client.user.tag}`);
    initializeZones(client);

    // Silently recreate threads for logged-in players
    for (const [userId, userData] of Object.entries(getData().users)) {
      if (isPlayerLoggedIn(userId) && userData.currentThreadId) {
        const zone = userData.currentZone.zone;
        const subzone = userData.currentZone.subzone;
        const zoneChannel = client.channels.cache.find(ch => ch.name === zone && ch.type === 0);
        if (zoneChannel) {
          await zoneChannel.threads.fetchActive();
          const threadName = `${zone}-${(await client.users.fetch(userId)).username}`;
          const existingThread = zoneChannel.threads.cache.find(
            t => t.name === threadName && !t.archived
          );
          if (!existingThread) {
            const thread = await zoneChannel.threads.create({
              name: threadName,
              autoArchiveDuration: 60,
              type: 11,
              invitable: false,
            });
            await thread.members.add(userId);
            await thread.members.add(client.user.id);
            setPlayerLoggedIn(userId, thread.id, zone, subzone); // Update thread ID
          }
        }
      }
    }
  });

  client.on('messageCreate', (message) => handleMessage(message, client));
  client.login(process.env.DISCORD_TOKEN);
}

module.exports = { startBot, client };