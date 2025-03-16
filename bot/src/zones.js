async function initializeZones(client) {
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
      }
    }
  }
}

module.exports = { initializeZones };