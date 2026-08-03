const fs = require('fs');
try {
  const code = fs.readFileSync('popup.js', 'utf8');
  new Function(code);
  console.log("Syntax is VALID!");
} catch (e) {
  console.error("Syntax Error:", e);
}
