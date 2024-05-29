# Mesh Spreadsheet

Mesh is a data and code editor that feels like a spreadsheet.

This is Mesh v3. The formula language is [ngn/k](https://codeberg.org/ngn/k), and the backend logic is also written in ngn/k.

This is a very early release, and it may not receive any updates. See [What needs work](#what-needs-work).

Sheets eval on each recalc, and those evals are not sandboxed! Take care with what you write in the formula bar.

![Mesh v3 demo](./demo.gif)

## Who is Mesh for?

Mesh is a spreadsheet program that fits into software's typical development and release workflows.

- calculations are stored as text files
- data can be of arbitrary length and defined structure (including empty data)
- data can optionally be stored in external files (eg `data.json`), instead of being stored in the sheet
- changes and releases can be managed via Git or other version control tools
- calculations can be run 'headlessly', independently of the program used to write the code.

If you maintain [load-bearing](https://xkcd.com/2347/) spreadsheets - files that are part of a processing pipeline - you might like Mesh.

## What Mesh does

### Usual spreadsheet things

- Write data straight into cells. If it's data, Mesh will try to figure out the datatype you meant.
- Formulas start with a `=` prefix: `=1+B2`.
- Press `F2` or click the formula bar to edit a formula instead of overwriting it. Precedents are highlighted in the grid.
- Hardcode cells look different to formula cells.
- Format cell contents using [Intl.NumberFormat syntax](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat). For example, highlight a cell and press `Ctrl-Shift-4` to show values in dollars.
- Cell names: toggle with `F3`. Change a cell's name by writing to its name cell. Mesh will update other cell formulas to use the new name.
- Connect to external data: drag a file onto the grid. For now, the file needs to be stored in the same folder as `server.py`.
- Quick calcs about the selected data (count, sum, average), shown above the code pane.
- Calculated table columns - add modified assignments below the top-level definition:
```
table:+`existingColumn!1 2 3
table[`newColumn]:1+table`existingColumn
```
### Unusual spreadsheet things

- A completely different - but very powerful - formula language.
- Sheets are stored as one or more text files, so that you can manage changes using Git. If you want to share it with someone, then manually zip the files into a folder.
- Data can optionally be stored in external files, while still being displayed in and being editable from the UI of your sheet. Just click where you want the data to 'live', open the hamburger menu, and drag-and-drop it under 'read-and-write files'. For now, the file needs to be stored in the same place as `server.py`.
- Headless calculations. You don't need to run Mesh to run a Mesh sheet - just ngn/k.
- Separate logic and presentation. If two data structures visually overlap, the calculations still work, because element cells don't get their own cell reference (they have to be referenced via their parent).
- Export results to files by adding an `exportTo` path in the cell's meta dict.

## What Mesh doesn't do

- Excel formulas ([OpenFormula](https://en.wikipedia.org/wiki/OpenFormula) compatibility).
- Excel file import ([OpenDocument](https://en.wikipedia.org/wiki/OpenDocument) 'zipped XML' sheets).
- Charting - instead, use an external program such as [Observable Framework](https://observablehq.com/framework/) to re-render charts on file change.
- Streaming data, or recalc when a file updates - instead, schedule or trigger data updates using cron or systemd timers.
- Case-insensitive cell references.

## Install

1. [Get and build ngn/k](https://codeberg.org/ngn/k).
2. Clone this repo.
3. Make sure you have Python 3 and its `websockets` module installed. In Ubuntu, the latter is `sudo apt install python3-websockets`.
4. Update the values in `vars.py`.
5. Run `server.py` - this starts the backend.
6. Start a second server to serve `index.html`. Try `python3 -m http.server` in the Mesh directory.
7. Go to `localhost:8000` in your browser.

## How does Mesh work?

Mesh sheets are stored as ngn/k code in text files. The sheet is shown in your web browser, the client; it's connected via WebSockets to a backend server that does calculations and updates files on your disk.

When you change a cell:

- the client sends an instruction to the server
- the server:
  - turns the sheet text into an abstract syntax tree (or 'AST')
  - modifies the cell's node in the tree
  - turns the tree back into code text (using [this ngn/k unparser](https://github.com/chrispsn/ngn-k-unparser))
  - re-runs the code text
  - passes visual info back to the client.

If the data you're editing is stored in a file that lives outside the sheet, the server will instead:

- update the data structure in memory
- serialise that data to text
- write that text to disk
- re-run the sheet calcs. 

Version 3 of Mesh updates cell calculation order when the sheet is written, not when it's run.

### Cell meta-info

Mesh records information that's just for the Mesh app as a dictionary that appears just above the data's definition. The Mesh app can still see it in the parse tree and extract info from it, but because that name is immediately redefined by the next line, it doesn't affect the calculations.

Here's a list that's named `amounts`, located at `G4`, and formatted in AUD:

```
amounts:`number`loc!(`style`currency!("currency";"AUD");`G4)
amounts:1 2 3
```

Here's a read-write table connection to the file `analysis.json`:

```
B2:`path!,"analysis.json"
B2:`j?1:"analysis.json"
```

Here's a calculation that's exported to the file `somePath.json`:

```
B2:`exportTo!,"somePath.json"
B2:1 2 3 4
```

## What needs work

### Features

- Obvious quality of life features: error handling, scrolling, undo/redo.
- Upstream issues in the unparser.
- Storing external data in directories other than that of `server.py`.
- A prettier code unparser and data serialiser, to make it easy to review changes via text comparison.
- No limit on the number of cells (which probably means changing the backend/calc language).
- Nicer data literals (which probably means changing the backend/calc language).
- Nested sheets and name lookup.
- Watching input files and automatically recalcing when they change.
- Cut-and-paste data.
- Pivot table wizard.
- Database connectivity, though that might be less important if (de-)serialisation is fast.
- Partial recalc from the point of change onwards, rather than recalculating the entire sheet on every change.
- Allowing an external program to swap out cell values with new ones so that sheets can be used as functions (eg swapping from test input to production input).
- Serialisation formats other than JSON and plain text. I'd like CSV and maybe [NDJSON](https://github.com/ndjson/ndjson-spec) or [JSONL](https://jsonlines.org/).
- A syntax that has nice dict and table literals and lets you specify expected/conversion types for external files.
- Sandboxing.
- A UI for editing calculated columns, and per-column formatting rules.

### Packaging

- A fully-in-browser WASM version, to make Mesh easier to try out.
- Electron (or similar?), so that Mesh can interact more with the filesystem without needing a server.
- A containerised (Dockerised?) version, to make installation easier.

### Deep dive: editable dicts and tables

Sheets can store data in external files, or in the sheet source itself. This section talks about the latter.

Mesh provides UI handles for editing list literals: inserting, deleting, or in-place edits of elements of simple lists such as `1 2 3` and general lists such as ```(1;`sym)```. It can do this because the ngn/k AST has special representations of list literals, instead of just making them a function call. Mesh can just look at the first item in an AST list node to figure out what to do.

But this approach isn't clean for dicts and tables, since the AST represents them as calls of functions that can do things other than make a data structure. For example, ngn/k uses `!` as make-dict and `+!` as make-table, but `!` has overloads such as 'mod'. General lists are also represented in the AST as a function call, but that function is internal-only ([`5:`](https://ngn.codeberg.page/k/#eJxLKFDSMLRO0FQCAAw8AjI=)), and it doesn't have any overloads, so Mesh knows that its arguments should be treated as list literal elements.

Conceivably Mesh could check the type and structure of the arguments to `!` (and generate a UI handle if the args are editable), but it makes the backend code complex. If Mesh did go down this route, it might be good to require editable tables to use a composition (```(+!)[`a;1 2]```) rather than a simple function call (```+![`a;1 2]```): that way, the make-table function would appear as an easy-to-recognise single-node composition (`(';+;!)`) instead of being split across nodes in the AST.

Ideally, Mesh's formula language would:

1. include special dict and table literal representations (ngn/k doesn't), that
2. have unique AST representations.

Potentially those representations could *literally* be dict and table data structures. Then the backend could just edit them like we would in userland, and they'd also be much easier for Mesh to losslessly unparse: if dict literals just appeared in the AST as `!` function calls, the unparser wouldn't know whether they intended a make-dict function call or a dict literal.

Ideally dict literals would be a list of key:value pairs, and table literals would be defined row-wise to flow with the portrait shape of a text file - even if that data was stored as columns behind the scenes.

## Why the k family? Why not Python or JavaScript?

Officially, ngn/k is [no longer supported](https://codeberg.org/ngn/k). But Mesh could potentially be ported to other k dialects or other languages.

To work with Mesh's approach to spreadsheets, the language needs certain features:

1. Its syntax should be simple and stable, so that it's (a) easy for Mesh to modify the AST and (b) fast to parse and unparse.
2. Formulas for simple data processing, such as sums and table joins, should be short.
3. It should have literals for lists, dicts, and tables. Those literals should have unique AST representations so that they are easy for Mesh to edit and can be losslessly round-tripped.

Bonus points if it has built-in serialisation formats (JSON, CSV) and is already on every machine or otherwise small enough to quickly download.

## Thank you

Thanks to Arthur Whitney for inventing and refining k, to ngn for his implementation of k6, and to my family and friends for their support.
