const fs = require("fs");
const path = require("path");
const root = process.argv[2];

for (const file of ["package.json", "package-lock.json"]) {
  const full = path.join(root, file);
  try {
    const obj = JSON.parse(fs.readFileSync(full, "utf8"));
    console.log(`${file}: VALID JSON`);
    console.log(`  name: ${obj.name ?? "(not set)"}`);
    console.log(`  lockfileVersion: ${obj.lockfileVersion ?? "(not applicable)"}`);
    for (const name of ["@azure/msal-browser", "@azure/msal-react"]) {
      const declared = obj.dependencies?.[name] ?? obj.devDependencies?.[name] ?? "(not declared)";
      const locked = obj.packages?.[`node_modules/${name}`]?.version ?? "(not locked)";
      if (file === "package.json") console.log(`  ${name} declared: ${declared}`);
      if (file === "package-lock.json") console.log(`  ${name} locked: ${locked}`);
    }
  } catch (e) {
    console.log(`${file}: INVALID OR UNREADABLE JSON: ${e.message}`);
    process.exitCode = 1;
  }
}
