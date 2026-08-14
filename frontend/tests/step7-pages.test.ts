import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function pageContent(relativePath: string): string {
  return readFileSync(resolve(process.cwd(), relativePath), "utf-8");
}

describe("Step 7 pages", () => {
  it("response page has no TBD placeholders", () => {
    const content = pageContent("app/response/page.tsx");
    expect(content.includes("TBD")).toBe(false);
  });

  it("roi page has no TBD placeholders", () => {
    const content = pageContent("app/roi/page.tsx");
    expect(content.includes("TBD")).toBe(false);
  });
});
