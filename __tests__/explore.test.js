jest.mock('../src/data', () => ({
  getData: jest.fn(),
  saveData: jest.fn()
}));

const { handleExplore } = require('../src/commands/explore');

describe('handleExplore', () => {
  let mockData;
  let mockMessage;

  beforeEach(() => {
    mockData = {
      users: {},
      defaultZone: 'cinthria',
      zones: {
        cinthria: {
          description: 'Welcome to the town of Cinthria!',
          subzones: {
            'temple-in-cinthria': 'A sacred temple'
          }
        }
      }
    };

    // Mock getData to return mockData
    require('../src/data').getData.mockReturnValue(mockData);
    // Mock saveData to update mockData
    require('../src/data').saveData.mockImplementation((updatedData) => {
      if (updatedData) mockData = updatedData; // Update mockData if data is passed
    });

    mockMessage = {
      channel: { type: 0, send: jest.fn() },
      author: { id: '123', username: 'testuser' },
      guild: {
        channels: {
          cache: {
            find: jest.fn().mockReturnValue({
              threads: {
                fetchActive: jest.fn(),
                cache: { find: jest.fn().mockReturnValue(null) },
                create: jest.fn().mockResolvedValue({
                  name: 'cinthria-testuser',
                  members: { add: jest.fn() },
                  send: jest.fn()
                })
              }
            })
          }
        }
      },
      reply: jest.fn(),
      client: { user: { id: 'bot123' } }
    };

    // Mock zoneUtils
    jest.mock('../src/commands/zoneUtils', () => ({
      getDefaultSubzone: jest.fn().mockReturnValue('temple-in-cinthria'),
      getZoneStatus: jest.fn().mockReturnValue('A sacred temple')
    }));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initializes new user and creates thread', async () => {
    await handleExplore(mockMessage);
    expect(mockMessage.reply).not.toHaveBeenCalled();
    expect(mockData.users['123']).toBeDefined();
    expect(mockData.users['123'].isLoggedIn).toBe(true);
    expect(mockData.users['123'].currentZone.zone).toBe('cinthria');
    expect(mockData.users['123'].currentZone.subzone).toBe('temple-in-cinthria');
  });

  test('rejects command in non-text channel', async () => {
    mockMessage.channel.type = 11;
    await handleExplore(mockMessage);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      'This command only works in text channels!'
    );
  });
});

