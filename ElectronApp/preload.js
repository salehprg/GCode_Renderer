
const { contextBridge, ipcRenderer } = require('electron');

console.log('Preload script loaded successfully');
contextBridge.exposeInMainWorld('electron', {
  openFolder: () => ipcRenderer.invoke('dialog:open-folder'),
});
