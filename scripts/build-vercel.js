const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const root = path.join(__dirname, '..');
const publicDir = path.join(root, 'public');
const indexFile = path.join(publicDir, 'index.html');

if (!fs.existsSync(indexFile)) {
  try {
    execSync('python scripts/build_netlify.py', { cwd: root, stdio: 'inherit' });
  } catch {
    console.error('Run "python scripts/build_netlify.py" locally before deploying.');
    process.exit(1);
  }
}

if (!fs.existsSync(indexFile)) {
  console.error('Missing public/index.html. Build the static site first.');
  process.exit(1);
}

console.log('Vercel static build ready.');
