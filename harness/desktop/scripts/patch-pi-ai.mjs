#!/usr/bin/env node
// Patch the staged pi-ai for Google's OpenAI-compatible layer: Gemini 3 models refuse a
// function call echoed back without the thought signature the model sent with it ("Function
// call is missing a thought_signature in functionCall parts", 400). pi-ai keeps no signature,
// so every tool round trip on Gemini failed. Google documents a bypass value for exactly this
// case; the patch attaches it to each echoed call when the base URL is Google's.
//
//   node scripts/patch-pi-ai.mjs            # after prepare-dsh.mjs; idempotent
//   node scripts/patch-pi-ai.mjs --check    # exit 1 when the staged file is not patched
//
// Remove once pi-ai carries the signature itself (upstream issue to be filed against
// @earendil-works/pi-ai, openai-completions.ts, convertMessages).
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const file = join(here, "..", "dsh", "node_modules", "@earendil-works", "pi-ai", "dist", "api", "openai-completions.js");
const MARK = "FOMO: Gemini thought signature";

const before = `                    return {
                        id: tc.id,
                        type: "function",
                        function: {
                            name: tc.name,
                            arguments: JSON.stringify(tc.arguments),
                        },
                    };
                });`;
const after = `                    const fnCall = {
                        id: tc.id,
                        type: "function",
                        function: {
                            name: tc.name,
                            arguments: JSON.stringify(tc.arguments),
                        },
                    };
                    // ${MARK}: Gemini 3 requires a signature on every echoed function call
                    if (String(model.baseUrl || "").includes("generativelanguage.googleapis.com")) {
                        fnCall.extra_content = { google: { thought_signature: "skip_thought_signature_validator" } };
                    }
                    return fnCall;
                });`;

const check = process.argv.includes("--check");
if (!existsSync(file)) {
  console.error(`patch-pi-ai: ${file} not found; run prepare-dsh.mjs first`);
  process.exit(check ? 1 : 0);
}
const text = readFileSync(file, "utf8");
if (text.includes(MARK)) {
  console.log("patch-pi-ai: already patched");
  process.exit(0);
}
if (check) {
  console.error("patch-pi-ai: not patched");
  process.exit(1);
}
if (!text.includes(before)) {
  console.error("patch-pi-ai: the expected block was not found; pi-ai changed, review the patch");
  process.exit(1);
}
writeFileSync(file, text.replace(before, after), "utf8");
console.log("patch-pi-ai: patched");
