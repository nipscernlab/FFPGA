const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

function createWindow() {
  // Criar janela do navegador
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#121212',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets/icons/app-icon.png'),
    show: false, // Não mostrar até que esteja pronto
    titleBarStyle: 'hiddenInset', // Barra de título mais elegante
    frame: false
  });

  // Carregar o arquivo index.html
  mainWindow.loadFile('index.html');

  // Abrir DevTools apenas em modo de desenvolvimento
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  // Mostrar a janela quando estiver pronta
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  // Responder a mensagens do renderizador
  ipcMain.on('app-maximize', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  });

  ipcMain.on('app-minimize', () => {
    mainWindow.minimize();
  });

  ipcMain.on('app-quit', () => {
    app.quit();
  });
}

// Criar janela quando o Electron estiver pronto
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // No macOS, é comum recriar uma janela quando
    // o ícone do dock é clicado e não há outras janelas abertas
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Sair quando todas as janelas estiverem fechadas (Windows & Linux)
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});