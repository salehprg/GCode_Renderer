
const { contextBridge, ipcRenderer } = require('electron');

console.log('Preload script loaded successfully');
console.log(process.cwd())


contextBridge.exposeInMainWorld('electron', {
  openFolder: () => ipcRenderer.invoke('dialog:open-folder'),
});
