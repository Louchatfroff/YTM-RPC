const SERVER_URL = 'http://localhost:8765';

// Fetch server state
async function checkServerStatus() {
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const state = document.getElementById('state');
  
  try {
    const response = await fetch(`${SERVER_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      statusDot.classList.remove('offline');
      statusText.textContent = 'Server connected';
      state.textContent = data.connected ? 'Discord connected' : 'Discord disconnected;
    }
  } catch (error) {
    statusDot.classList.add('offline');
    statusText.textContent = 'Server offline';
    state.textContent = 'Start Python Server';
  }
}

// Fetch current informations
async function getCurrentInfo() {
  const currentSong = document.getElementById('currentSong');
  
  try {
    const response = await fetch(`${SERVER_URL}/current`);
    if (response.ok) {
      const data = await response.json();
      if (data.title) {
        currentSong.textContent = `${data.title} - ${data.artist}`;
      }
    }
  } catch (error) {
    currentSong.textContent = 'None';
  }
}

// Open YTM
document.getElementById('openYT').addEventListener('click', () => {
  chrome.tabs.create({ url: 'https://music.youtube.com' });
});

// Help link
document.getElementById('helpLink').addEventListener('click', (e) => {
  e.preventDefault();
  window.open('https://github.com/Louchatfroff/YTM-RPC/tree/main', '_blank');
});

// Periodic update
checkServerStatus();
getCurrentInfo();
setInterval(() => {
  checkServerStatus();
  getCurrentInfo();
}, 5000);
