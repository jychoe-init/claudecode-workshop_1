import assert from "node:assert/strict";
import { greet } from "./src/greet.js";

assert.equal(greet("Claude"), "Hello, Claude!");
console.log("PASS");
