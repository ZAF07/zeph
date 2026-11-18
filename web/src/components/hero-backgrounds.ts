/**
 * The illustrated backgrounds and heights of the page heroes, phone first
 * and from 900px up. The `background` values are copied from the Images
 * section of `design/README.md`, with only the `url()` path changed.
 */
export const heroBackgrounds = {
  home: "min-h-[402px] min-[900px]:min-h-[230px] [background:linear-gradient(180deg,#0A202C_0%,#0A202C_24%,rgba(10,32,44,.6)_42%,rgba(10,32,44,0)_58%),url(/design/home-bench.jpg)_right_bottom/auto_78%_no-repeat_#0A202C] min-[900px]:[background:linear-gradient(90deg,rgba(10,32,44,.82)_0%,rgba(10,32,44,.55)_42%,rgba(10,32,44,0)_68%),url(/design/home-bench.jpg)_right_64%/cover_no-repeat_#0A202C]",
  memories:
    "min-h-[472px] min-[900px]:min-h-[270px] [background:linear-gradient(180deg,#0A202C_0%,#0A202C_24%,rgba(10,32,44,.6)_42%,rgba(10,32,44,0)_58%),url(/design/memories-niches.jpg)_right_bottom/auto_78%_no-repeat_#0A202C] min-[900px]:[background:linear-gradient(90deg,rgba(10,32,44,.82)_0%,rgba(10,32,44,.55)_42%,rgba(10,32,44,0)_68%),url(/design/memories-niches.jpg)_right_64%/cover_no-repeat_#0A202C]",
  checkIns:
    "min-h-[472px] min-[900px]:min-h-[270px] [background:linear-gradient(180deg,#0A202C_0%,#0A202C_24%,rgba(10,32,44,.6)_42%,rgba(10,32,44,0)_58%),url(/design/checkins-beacon.jpg)_right_bottom/auto_78%_no-repeat_#0A202C] min-[900px]:[background:linear-gradient(90deg,rgba(10,32,44,.82)_0%,rgba(10,32,44,.55)_42%,rgba(10,32,44,0)_68%),url(/design/checkins-beacon.jpg)_right_64%/cover_no-repeat_#0A202C]",
};

/** Which page hero to draw. */
export type HeroBackground = keyof typeof heroBackgrounds;
