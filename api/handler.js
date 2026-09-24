const { handler } = require('../lib/handler');

module.exports = async (req, res) => {
  const url = new URL(req.url, `https://${req.headers.host || 'localhost'}`);
  const path = url.pathname.replace(/\/$/, '') || '/';

  let body = '';
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    if (typeof req.body === 'string') {
      body = req.body;
    } else if (req.body && Object.keys(req.body).length) {
      body = JSON.stringify(req.body);
    }
  }

  const event = {
    httpMethod: req.method,
    path,
    headers: req.headers,
    queryStringParameters: Object.fromEntries(url.searchParams.entries()),
    body,
  };

  const result = await handler(event);
  res.status(result.statusCode);
  Object.entries(result.headers || {}).forEach(([key, value]) => {
    res.setHeader(key, value);
  });
  res.send(result.body);
};
