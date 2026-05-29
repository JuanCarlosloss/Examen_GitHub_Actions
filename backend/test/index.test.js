import { handleRequest } from '../src/index.js';

if (handleRequest() !== "backend_ok") {
  throw new Error("Backend test failed!");
}
console.log("Backend test passed successfully.");
