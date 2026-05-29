import { main } from '../src/index.js';

if (main() !== "frontend_ok") {
  throw new Error("Frontend test failed!");
}
console.log("Frontend test passed successfully.");
