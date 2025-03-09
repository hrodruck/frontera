const { getZoneStatus, getDefaultSubzone } = require('../src/commands/zoneUtils');

describe('src/commands/zoneUtils', () => {
  const mockData = {
    zones: {
      cinthria: {
        description: 'Welcome to the town of Cinthria!',
        subzones: {
          'temple-in-cinthria': 'A sacred temple with ancient carvings on the walls.'
        }
      },
      'cinthria-wilds': '7 dogs, 4 bandits left'
    }
  };

  beforeAll(() => {
    jest.mock('../src/data', () => ({
      getData: () => mockData
    }));
  });

  describe('getZoneStatus', () => {
    test('returns status for zone without subzone', () => {
      const status = getZoneStatus('cinthria-wilds', null);
      expect(status).toBe('7 dogs, 4 bandits left');
    });

    test('returns combined status for zone with subzone', () => {
      const status = getZoneStatus('cinthria', 'temple-in-cinthria');
      expect(status).toBe(
        'Welcome to the town of Cinthria!\ntemple-in-cinthria: A sacred temple with ancient carvings on the walls.'
      );
    });

    test('returns no status message for unknown zone', () => {
      const status = getZoneStatus('unknown', null);
      expect(status).toBe('No status available yet.');
    });
  });

  describe('getDefaultSubzone', () => {
    test('returns default subzone for cinthria', () => {
      expect(getDefaultSubzone('cinthria')).toBe('temple-in-cinthria');
    });

    test('returns null for zone without default subzone', () => {
      expect(getDefaultSubzone('cinthria-wilds')).toBe(null);
    });
  });
});
