import fs from 'fs';
let content = fs.readFileSync('frontend/src/components/Layout.jsx', 'utf8');

content = content.replace(
    /if \(user\?.role_id === 1\) \{/,
    `const isAdmin = user?.role_name === 'System Administrator' || user?.permissions?.some(p => p.module === 'Admin');
  if (isAdmin) {`
);

fs.writeFileSync('frontend/src/components/Layout.jsx', content);
console.log('Layout patched');
