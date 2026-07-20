/**
 * Simple Static File Server for TRAVAS-AI Frontend
 * Serves the HTML UI on port 8000
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8000;
const FRONTEND_DIR = __dirname;

const server = http.createServer((req, res) => {
  // Default to index.html
  let filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(FRONTEND_DIR, filePath);

  // Security: prevent directory traversal
  if (!filePath.startsWith(FRONTEND_DIR)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('Forbidden');
    return;
  }

  // Read file
  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/html' });
      res.end('<h1>404 - File Not Found</h1>', 'utf-8');
      return;
    }

    // Set content type
    let contentType = 'text/plain';
    if (filePath.endsWith('.html')) contentType = 'text/html';
    else if (filePath.endsWith('.js')) contentType = 'application/javascript';
    else if (filePath.endsWith('.css')) contentType = 'text/css';

    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
});

server.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║        TRAVAS-AI Frontend Server Started                   ║
║                                                            ║
║  Frontend: http://localhost:${PORT}                           ║
║  API Server: http://localhost:3000 (must be running)      ║
║                                                            ║
║  Make sure Node.js API Gateway is running first:          ║
║    cd api/                                                 ║
║    npm install                                             ║
║    npm start                                               ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
  `);
});
