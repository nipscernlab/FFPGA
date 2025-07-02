const { contextBridge, ipcRenderer } = require('electron');

// Expor APIs seguras para o processo de renderização
contextBridge.exposeInMainWorld('electronAPI', {
  // Controles de janela
  windowControl: {
    minimize: () => ipcRenderer.send('app-minimize'),
    maximize: () => ipcRenderer.send('app-maximize'),
    quit: () => ipcRenderer.send('app-quit')
  },
  
  // Outras APIs que podemos precisar
  getAppVersion: () => process.env.npm_package_version,
  platform: process.platform
});