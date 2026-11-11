import { describe, expect, it } from "vitest";

import { countryFromBrowser, countryOptions } from "@/lib/countries";

describe("countryFromBrowser", () => {
  it("reads the country from the first language that names one", () => {
    expect(countryFromBrowser(["en", "en-SG"])).toBe("SG");
  });

  it("gives null when no language names a country", () => {
    expect(countryFromBrowser(["en", "zh"])).toBeNull();
  });

  it("skips languages it cannot read", () => {
    expect(countryFromBrowser(["not a language", "ms-MY"])).toBe("MY");
  });
});

describe("countryOptions", () => {
  it("names each country in English, sorted by name", () => {
    const options = countryOptions();
    const names = options.map((option) => option.name);

    expect(options).toContainEqual({ code: "SG", name: "Singapore" });
    expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b)));
  });
});
