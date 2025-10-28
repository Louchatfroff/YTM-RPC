// Local server config
const SERVER_URL = 'http://localhost:8765';
let currentMusicInfo = null;

// Écoute les messages du content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'MUSIC_UPDATE') {
    currentMusicInfo = message.data;
    sendToServer(message.data);
  }
});

// Send Data to python server
async function sendToServer(data) {
  try {
    const response = await fetch(`${SERVER_URL}/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      console.error('Server Error:', response.status);
    }
  } catch (error) {
    console.error('Failed To Connect To Server:', error);
  }
}

// Periodic ping
setInterval(async () => {
  if (currentMusicInfo && !currentMusicInfo.isPaused) {
    sendToServer(currentMusicInfo);
  }
}, 10000);

// Connection Managing
chrome.runtime.onStartup.addListener(() => {
  checkServerConnection();
});

chrome.runtime.onInstalled.addListener(() => {
  checkServerConnection();
});

async function checkServerConnection() {
  try {
    const response = await fetch(`${SERVER_URL}/health`);
    if (response.ok) {
      console.log('Python Server Connected!');
    }
  } catch (error) {
    console.warn('Python Server Unavailable, Make Sure It Is Running..');
  }
}
