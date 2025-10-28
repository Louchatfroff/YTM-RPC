// Fetch YTM Data
function extractMusicInfo() {
  const videoElement = document.querySelector('video');
  const titleElement = document.querySelector('.title.style-scope.ytmusic-player-bar');
  const artistElement = document.querySelector('.byline.style-scope.ytmusic-player-bar');
  const thumbnailElement = document.querySelector('.ytmusic-player-bar img');
  
  if (!videoElement || !titleElement) {
    return null;
  }

  const isPaused = videoElement.paused;
  const currentTime = Math.floor(videoElement.currentTime);
  const duration = Math.floor(videoElement.duration);
  const title = titleElement.textContent.trim();
  const artist = artistElement ? artistElement.textContent.trim() : 'Artiste inconnu';
  const thumbnail = thumbnailElement ? thumbnailElement.src : '';
  
  return {
    title,
    artist,
    thumbnail,
    currentTime,
    duration,
    isPaused,
    timestamp: Date.now()
  };
}

// Send Data To Worker Services
function sendMusicInfo() {
  const info = extractMusicInfo();
  if (info) {
    chrome.runtime.sendMessage({
      type: 'MUSIC_UPDATE',
      data: info
    });
  }
}

// Observe To Detect Changes
let observer;
let lastTitle = '';

function startObserver() {
  const targetNode = document.querySelector('ytmusic-player-bar');
  if (!targetNode) {
    setTimeout(startObserver, 1000);
    return;
  }

  observer = new MutationObserver(() => {
    const info = extractMusicInfo();
    if (info && info.title !== lastTitle) {
      lastTitle = info.title;
      sendMusicInfo();
    }
  });

  observer.observe(targetNode, {
    childList: true,
    subtree: true,
    characterData: true
  });

  // Initial Sending
  sendMusicInfo();
}

// Listen For Playing Events
function setupVideoListeners() {
  const videoElement = document.querySelector('video');
  if (!videoElement) {
    setTimeout(setupVideoListeners, 1000);
    return;
  }

  videoElement.addEventListener('play', sendMusicInfo);
  videoElement.addEventListener('pause', sendMusicInfo);
  videoElement.addEventListener('timeupdate', () => {
    // Send Every 5 seconds
    if (Math.floor(videoElement.currentTime) % 5 === 0) {
      sendMusicInfo();
    }
  });
}

// Initialisation
startObserver();
setupVideoListeners();

// Periodically Maintaining Connection
setInterval(sendMusicInfo, 15000);
