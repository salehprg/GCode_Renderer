const { app, BrowserWindow, dialog, ipcMain} = require('electron');
const path = require('path');

const express = require('express');
const server = express();
const port = 3001;
server.use(express.static(path.join(__dirname, '../FrontApp/build/'))); // Serve React build files

server.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1024,
        height: 720,
        webPreferences: {
            contextIsolation: true, // Enable context isolation
            enableRemoteModule: false, // Disable the remote module for security
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.loadURL(`http://localhost:${port}`);

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

ipcMain.handle('dialog:open-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'], // Select folder
    });

    return result.filePaths; // Returns an array of selected folder paths
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
