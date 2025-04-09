// Simple script to start the Puppeteer MCP server

try {
  // Try to directly run the server
  const serverPath = 'C:\\Users\\mille\\OneDrive\\Documents\\Cline\\MCP\\puppeteer-server\\node_modules\\@modelcontextprotocol\\server-puppeteer';
  require(serverPath);
  console.log('Puppeteer MCP server started successfully');
} catch (error) {
  console.error('Error starting Puppeteer MCP server:', error);
}
