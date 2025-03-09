jest.mock('../src/data', () => ({
  getData: jest.fn(),
  saveData: jest.fn()
}));

const { handleMove } = require('../src/commands/move');

describe('handleMove', () => {
  let mockMessage;
  let mockData;

  beforeEach(() => {
    mockData = {
      users: {
        '123': {
          currentZone: { zone: 'cinthria', subzone: null },
          zones: {}
        }
      },
      zones: {
        cinthria: {
          subzones: {
            'temple-in-cinthria': 'A sacred temple',
            'market-square': 'A bustling market'
          }
        }
      }
    };

    // Reset and set mock implementation
    require('../src/data').getData.mockReturnValue(mockData);
    require('../src/data').saveData.mockReset();

    jest.mock('../src/commands/zoneUtils', () => ({
      getZoneStatus: jest.fn().mockReturnValue('A sacred temple')
    }));

    mockMessage = {
      author: { id: '123', username: 'testuser' },
      reply: jest.fn()
    };
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('moves to valid subzone from null', async () => {
    await handleMove(mockMessage, ['temple-in-cinthria']);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      expect.stringContaining('you move to cinthria (temple-in-cinthria)')
    );
    expect(mockData.users['123'].currentZone.subzone).toBe('temple-in-cinthria');
  });

  test('prevents moving to same subzone', async () => {
    mockData.users['123'].currentZone.subzone = 'temple-in-cinthria';
    await handleMove(mockMessage, ['temple-in-cinthria']);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      "You're already in temple-in-cinthria!"
    );
  });

  test('lists subzones when no args provided', async () => {
    await handleMove(mockMessage, []);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      expect.stringContaining('Available subzones in cinthria: temple-in-cinthria, market-square')
    );
  });

  test('rejects move to invalid subzone', async () => {
    await handleMove(mockMessage, ['invalid']);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      expect.stringContaining('Subzone "invalid" not found')
    );
  });
});

