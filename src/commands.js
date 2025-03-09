const { getData } = require('./data');
const { handleExplore } = require('./commands/explore');
const { handleGoodbye } = require('./commands/goodbye');
const { handleLook } = require('./commands/look');
const { handleMove } = require('./commands/move');

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
      // Check if user is logged in and message is in their thread
      const userData = data.users[userId];
      const isLoggedIn = userData?.isLoggedIn;

      if (!userData || !isLoggedIn) {
        await message.reply("You need to be logged in with !explore to use this command!");
        return;
      }

      // Check if message is in a thread and matches the user's thread
      if (message.channel.type !== 11) { // 11 is GUILD_PUBLIC_THREAD
        await message.reply("This command must be used in your active exploration thread!");
        return;
      }

      const expectedThreadName = `${userData.currentZone.zone}-${message.author.username}`;
      if (message.channel.name !== expectedThreadName) {
        await message.reply("This command must be used in your own active exploration thread!");
        return;
      }

      // Handle commands that require being logged in and in the thread
      if (command === 'look') {
        await handleLook(message);
      } else if (command === 'move') { 
        await handleMove(message, args);
      }
    
    }
  } catch (error) {
    console.error('Error handling message:', error);
  }
}

module.exports = { handleMessage };