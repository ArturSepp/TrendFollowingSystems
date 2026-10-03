"""Prepare and compile the approved manuscript assets outside the checkout."""

from pathlib import Path
import shutil
import subprocess

from papers.tf_systems.replication.paths import PAPER_DIR, output_root


def prepare_build() -> Path:
    """Copy exactly the existing approved paper inputs into an external build tree."""
    destination = output_root() / "latex-build"
    destination.mkdir(parents=True, exist_ok=True)
    for line in (PAPER_DIR / ".gitignore").read_text(encoding="utf-8").splitlines():
        if not line.startswith("!/paper/") or line.endswith("/"):
            continue
        relative = Path(line[len("!/paper/"):])
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PAPER_DIR / "paper" / relative, target)
    return destination


def main() -> None:
    """Run three pdflatex passes without overwriting the manuscript sources."""
    destination = prepare_build()
    for _ in range(3):
        subprocess.run(["pdflatex", "-halt-on-error", "-interaction=nonstopmode",
                        "TrendFollowing_PaperA_SIFIN_v1.tex"], cwd=destination, check=True)
    print(destination / "TrendFollowing_PaperA_SIFIN_v1.pdf")


if __name__ == "__main__":
    main()
