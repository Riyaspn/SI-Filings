const fs = require('fs');
const code = fs.readFileSync('popup.js', 'utf8');

let openBraces = 0;
let lines = code.split('\n');
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  for (let j = 0; j < line.length; j++) {
    if (line[j] === '{') openBraces++;
    else if (line[j] === '}') openBraces--;
  }
}
console.log("Net braces:", openBraces);
