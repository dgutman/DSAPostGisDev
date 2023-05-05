const path = require('path');
const express = require('express');
const reload = require('reload');
const http = require('http');

const app = express();
const port = 9777; // "xprs" in T9

app.use(express.static("."))

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname + '/index.html'));
});


const server = http.createServer(app);

server.listen(port, function() {
    console.log('Listening on port %d', port);
 
    // if (process.send) {
    //     process.send('online');
    // }
})

reload(app);

// const livereload = require('livereload');
// const reload = livereload.createServer();
// reload.watch(__dirname + "/server.js");
// reload.watch("webixOSDViewer.html")

// // const browserSync = require('browser-sync')
// // const shrinkRay = require('shrink-ray');

