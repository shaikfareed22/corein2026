import { describe, expect, it } from "vitest";
import { asIdea, catalogue } from "./index";

// The three copies of the catalogue, as text: ours, the Android asset, the harness asset.
const COPIES = import.meta.glob<string>(
  ["./ideas.*.json", "../../../android/src/android/app/src/main/assets/nanomuse/ideas.*.json", "../../../harness/dsh-nanomuse/assets/ideas.*.json"],
  { query: "?raw", import: "default", eager: true },
);
const copy = (suffix: string) => Object.entries(COPIES).find(([k]) => k.endsWith(suffix))?.[1];

describe("the Ideas catalogue", () => {
  it.each(["en"])("ideas.%s.json is identical to the Android and harness copies (contract C5)", (lang) => {
    const ours = copy(`/src/ideas/ideas.${lang}.json`) ?? copy(`./ideas.${lang}.json`);
    const android = copy(`/assets/nanomuse/ideas.${lang}.json`);
    const harness = copy(`/dsh-nanomuse/assets/ideas.${lang}.json`);
    expect(ours, "our copy").toBeTruthy();
    expect(android, "the Android asset").toBeTruthy();
    expect(harness, "the harness asset").toBeTruthy();
    expect(ours === android, `web/src/ideas/ideas.${lang}.json differs from the Android asset`).toBe(true);
    expect(ours === harness, `web/src/ideas/ideas.${lang}.json differs from the harness asset`).toBe(true);
  });

  it("has six sections of four ideas, the same list for every locale", () => {
    const en = catalogue("en");
    expect(en.sections.map((s) => s.id)).toEqual(["travel", "work", "life", "learn", "family", "more"]);
    for (const s of en.sections) {
      expect(s.ideas).toHaveLength(4);
    }
    expect(catalogue("fr")).toBe(en);
    expect(catalogue("zh-CN")).toBe(en);
  });

  it("turns a catalogue idea into the page's shape", () => {
    const routine = catalogue("en").sections.flatMap((s) => s.ideas).find((x) => x.kind === "ROUTINE")!;
    const idea = asIdea(routine);
    expect(idea.kind).toBe("routine");
    expect(idea.time).toMatch(/^\d{2}:\d{2}$/);
    expect(idea.detail).toBe(routine.body);
    expect(idea.emoji).toBe(routine.emoji);
  });
});
