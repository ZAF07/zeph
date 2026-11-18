# Prompts for Claude Code

Paste these as they are. Run them from the `web` folder.

## Once, at the start

```
Read design/README.md in full, then open design/reference/Dashboard.html, design/reference/M-Dashboard.html and design/tokens.css. Do not write any code yet.

Reply with: (1) the one rule in your own words, (2) how you will know a page is finished, (3) the build order, (4) every question you have before slice 0. Then wait for me.
```

## For each slice

```
Do slice N from design/README.md, and only slice N.

Before coding, open every reference file that slice names, at both widths, and list the parts you will build. Build them so the computed styles equal the inline styles in the reference. Take copy, sizes, colours, gaps and image CSS from the reference, never from memory.

When done: run node design/compare.cjs for this slice's refs, plus pnpm lint, pnpm typecheck and pnpm test. Paste the PASS/FAIL lines. If anything fails, fix the app and rerun. Do not change design/, LIMIT, masks or baselines. List anything you were unsure about or chose yourself. Then stop.
```

## If a page will not pass

```
<Ref> is failing. Open design/.diff/<Ref>.png and design/baseline/<Ref>.png, tell me exactly which regions differ and why, then fix the app. Do not touch the test.
```

## If Claude Code suggests changing the design

```
No. The reference is fixed. If you think it is wrong, describe the problem and wait for me.
```
