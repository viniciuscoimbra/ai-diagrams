# Comparison table

Editorial page with one or more `table.comp` tables. It uses the same `style.css` and the same `build.py` as the posters. No canvas and no arrows: the lint exempts badges and steps because the document has no `<svg class="edges">`.

Template: `templates/05-comparison-table/`, in the skill folder.

## Anatomy

| Element | Class | Content |
|---|---|---|
| Frame | `.hdr`, `.kicker`, `h1`, `.sub`, `.foot` | same as the poster; the `h1` names what is being compared |
| Section title | `.sec` | one per table, in caps |
| Table | `table.comp` | first row with `th`; the first column is the criterion, in bold |
| Decision row | `tr.escolha` (template's local CSS) | the adopted option and the condition to revisit it, in one cell with `colspan` |
| Note | `.nota` (local CSS) | one reading sentence below the table |

## Rules

- Criterion in the row, option in the column. Up to four options per table; more than that becomes two tables.
- Short cell, no final period, in technical register. Market terms in English (shard, consumer group, replay).
- The last row records the choice when the table supports a decision. A comparison without a choice does not get that row.
- Cost goes in as a form (what it charges for) and never as an invented value: a number comes from a measurement or a calculator.

## Width: the table has to fit

The page is 1760px wide and the content, between the margins, 1664px. The capture cuts whatever goes past that, and the gate fails with `OVERFLOW`.

- `table.comp` already comes with `width:100%` and `table-layout:fixed`: the column widths come from the first row (`th`), not from the cell text. Do not switch to `table-layout:auto`.
- The first column (criterion) is 220px; the others split the rest equally. For another split, give `width` to the `th` elements in the local `<style>`, adding up to 1664px. For example, criterion and three options: `table.comp th:first-child{width:220px}` and the three options without a width (1444px divided by three).
- Never use `white-space:nowrap` on a text cell: the cell wraps, the table does not stretch.
- Up to four options per table. With more, split into two tables or declare a wider page with `<meta name="width" content="N">` in the `<head>`; the build captures at that width.
- A long cell wraps into many lines: shorten the text instead of widening the column.

## Commands

```bash
python3 <skill>/scripts/build.py diagrams/_src/NN-comparison.html
```

The build measures the page height on its own. Look at the PNG: a cell wrapping into many lines calls for shorter text, not a wider column.
