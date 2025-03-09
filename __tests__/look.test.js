jest.mock('../src/data', () => ({
  getData: jest.fn(),
  saveData: jest.fn()
}));

const { handleLook } = require('../src/commands/look');

describe('handleLook', () => {
  let mockMessage;
  let mockData;

  beforeEach(() => {
    mockData = {
      users: {
        '123': {
          currentZone: { zone: 'cinthria', subzone: 'temple-in-cinthria' },
          zones: {
            cinthria: {
              hasSeenMessage: false,
              subzones: { 'temple-in-cinthria': { hasSeenMessage: false } }
            }
          }
        }
      },
      zones: {
        cinthria: {
          description: 'Welcome to Cinthria!',
          subzones: { 'temple-in-cinthria': 'A sacred temple' }
        }
      }
    };

    // Reset and set mock implementation
    require('../src/data').getData.mockReturnValue(mockData);
    require('../src/data').saveData.mockReset();

    mockMessage = {
      author: { id: '123' },
      reply: jest.fn()
    };
  });

  test('shows zone and subzone description for first look', async () => {
    await handleLook(mockMessage);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      'Welcome to Cinthria!\nA sacred temple'
    );
    expect(mockData.users['123'].zones.cinthria.hasSeenMessage).toBe(true);
    expect(mockData.users['123'].zones.cinthria.subzones['temple-in-cinthria'].hasSeenMessage).toBe(true);
  });

  test('shows reminder message for subsequent looks', async () => {
    mockData.users['123'].zones.cinthria.hasSeenMessage = true;
    mockData.users['123'].zones.cinthria.subzones['temple-in-cinthria'].hasSeenMessage = true;
    await handleLook(mockMessage);
    expect(mockMessage.reply).toHaveBeenCalledWith(
      'Nothing new to see here. As a reminder, here you are:\ncinthria (temple-in-cinthria)\nA sacred temple'
    );
  });
});

