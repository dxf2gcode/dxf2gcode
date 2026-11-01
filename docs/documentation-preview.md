# Documentation preview

This prototype uses [Zensical](https://zensical.org/docs/get-started/), configured
in `zensical.toml` at the repository root. The development website is hosted
with GitHub Pages. Publishing uses a separate manual GitHub Actions workflow
on `develop`; local builds and automatic documentation checks never deploy.

## Requirements

- Python 3.11 or newer with `pip` and `venv`.
- The packages in `requirements-docs.txt`, including Zensical 0.0.74.
- Internet access for the initial package installation.

The documentation environment is independent of the Qt application and does not
require PyQt, a Rust compiler or the application build. Use system fonts; the
site does not request Google Fonts. Zensical supplies the client-side search.

## Windows PowerShell

Run these commands from PowerShell. Replace the checkout path if necessary:

```powershell
Set-Location D:\GIT\dxf2gcode-sourcecode
py -3.11 -m venv .tox\docs
& .\.tox\docs\Scripts\python.exe -m pip install -r requirements-docs.txt
& .\.tox\docs\Scripts\python.exe -m zensical serve
```

Open <http://127.0.0.1:8000/> in your browser. Stop the server with **Ctrl+C**.
The commands call the environment's Python directly, so activating a PowerShell
script or changing the execution policy is unnecessary.

After the first installation, only the last command is needed to start the
preview. If Python 3.11 is not installed, select an installed Python version
of at least 3.11 instead.

## Build and check

From the repository root:

```powershell
& .\.tox\docs\Scripts\python.exe -m zensical build --strict
```

The generated website is written to `.tox/docs-site/`. Internal page links and
anchors are validated during the build. The build does not publish anything.

For a quick browser check, open the [introduction](introduction.md), check the
logo on the [home page](index.md), and search for **postprocessor**. A result
should lead to the introduction. Do not open generated HTML through `file://`;
use the local server so that search and assets load correctly.
