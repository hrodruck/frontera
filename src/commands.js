const { getData } = require('./data');
const { handleExplore } = require('./commands/explore');
const { handleGoodbye } = require('./commands/goodbye');
const { handleLook } = require('./commands/look');
const { handleMove } = require('./commands/move');
const { handleSpk } = require('./commands/spk');

async function handleMessage(message) {
  if (message.author.bot || !message.content.startsWith('!')) return;

  const args = message.content.slice(1).trim().split(/ +/);
  const command = args.shift().toLowerCase();
  const data = getData();
  const userId = message.author.id;

  try {
    if (command === 'explore') {
      await handleExplore(message);
    } else if (command === 'goodbye') {
      await handleGoodbye(message);
    } else {
      const userData = data.users[userId];
      const isLoggedIn = userData?.isLoggedIn;

      if (!userData || !isLoggedIn) {
        await message.reply("You need to be logged in with !explore to use this command!");
        return;
      }

      if (message.channel.type !== 11) {
        await message.reply("This command must be used in your active exploration thread!");
        return;
      }

      const expectedThreadName = `${userData.currentZone.zone}-${message.author.username}`;
      if (message.channel.name !== expectedThreadName) {
        await message.reply("This command must be used in your own active exploration thread!");
        return;
      }

      if (command === 'look') {
        await handleLook(message);
      } else if (command === 'move') { 
        await handleMove(message, args);
      } else if (command === 'spk') {
        await handleSpk(message, args);
      }
    }
  } catch (error) {
    console.error('Error handling message:', error);
    await message.reply('Something went wrong!');
  }
}

module.exports = { handleMessage };

