const { getData } = require('./data');

function loadZones() {
  const data = getData();
  try {
    // Convert zone keys to proper case (e.g., "cinthria" -> "Cinthria")
    return Object.keys(data.zones).map((zone) =>
      zone
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    );
  } catch (error) {
    console.error('Failed to process zones from data:', error);
    // Fallback to default zones if processing fails
    return ['Cinthria', 'Cinthria Wilds', 'Swamps', 'The Shattered Crypt'];
  }
}

async function initializeZones(client) {
  const zones = loadZones();

  for (const guild of client.guilds.cache.values()) {
    let fronteraCategory = guild.channels.cache.find(
      (ch) => ch.type === 4 && ch.name.toLowerCase() === 'frontera'
    );

    if (!fronteraCategory) {
      try {
        fronteraCategory = await guild.channels.create({
          name: 'Frontera',
          type: 4,
        });
        console.log(`Created Frontera category in ${guild.name}`);
      } catch (error) {
        console.error(`Failed to create Frontera category in ${guild.name}:`, error);
        continue;
      }
    }

    for (const zone of zones) {
      const channelName = zone.toLowerCase().replace(/ /g, '-');
      const existingChannel = guild.channels.cache.find(
        (ch) => ch.name === channelName && ch.parentId === fronteraCategory.id
      );

      if (!existingChannel) {
        try {
          await guild.channels.create({
            name: channelName,
            type: 0,
            parent: fronteraCategory.id,
          });
          console.log(`Created #${channelName} under Frontera in ${guild.name}`);
        } catch (error) {
          console.error(`Failed to create #${channelName} in ${guild.name}:`, error);
        }
      }
    }
  }
}

module.exports = { initializeZones };