const SERVER_URL = 'http://localhost:8765';

// Vérifier l'état du serveur
async function checkServerStatus() {
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const state = document.getElementById('state');
  
  try {
    const response = await fetch(`${SERVER_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      statusDot.classList.remove('offline');
      statusText.textContent = 'Serveur connecté';
      state.textContent = data.connected ? 'Discord connecté' : 'Discord déconnecté';
    }
  } catch (error) {
    statusDot.classList.add('offline');
    statusText.textContent = 'Serveur hors ligne';
    state.textContent = 'Démarrez le serveur Python';
  }
}

// Récupérer les infos actuelles
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
    currentSong.textContent = 'Aucune';
  }
}

// Ouvrir YouTube Music
document.getElementById('openYT').addEventListener('click', () => {
  chrome.tabs.create({ url: 'https://music.youtube.com' });
});

// Lien d'aide
document.getElementById('helpLink').addEventListener('click', (e) => {
  e.preventDefault();
  alert('Instructions:\n\n1. Installez les dépendances Python: pip install pypresence flask flask-cors\n2. Lancez le serveur: python server.py\n3. Ouvrez YouTube Music et lancez une musique\n4. Votre activité apparaîtra sur Discord!');
});

// Mise à jour périodique
checkServerStatus();
getCurrentInfo();
setInterval(() => {
  checkServerStatus();
  getCurrentInfo();
}, 5000);