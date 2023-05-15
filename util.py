from dataclasses import dataclass
from pathlib import Path
import re
import shutil

# \subfile{content/1/section.tex}
RE_PART = re.compile(r"\\subfile{content/(?P<part>\d+)/section.tex}")
# \subfile{content/1/chapter1/0.tex}
RE_CH_SEC = re.compile(
    r"\\subfile{content/(?P<part>\d+)/chapter(?P<ch>\d+)/(?P<sec>\d+).tex}"
)


@dataclass
class Part:
    part_num: int
    title: str

    def old_path(self) -> Path:
        path = Path(f"content/{self.part_num}/Part-{self.part_num}.tex")
        assert path.exists()
        return path

    def new_path(self):
        path = Path(f"content/part{self.part_num}.tex")
        return path


@dataclass
class Chapter:
    part_num: int
    ch_num: int
    title: str

    def old_path(self) -> Path:
        path = Path(f"content/{self.part_num}/chapter{self.ch_num}/0.tex")
        assert path.exists()
        return path

    def new_path(self):
        path = Path(f"content/part{self.part_num}/ch{self.ch_num}.tex")
        return path

    def old_folder(self):
        path = Path(f"content/{self.part_num}/chapter{self.ch_num}")
        return path

    def new_folder(self):
        path = Path(f"content/part{self.part_num}/ch{self.ch_num}")
        return path


@dataclass
class Section:
    part_num: int
    ch_num: int
    sec_num: int
    title: str

    def old_path(self) -> Path:
        path = Path(f"content/{self.part_num}/chapter{self.ch_num}/{self.sec_num}.tex")
        assert path.exists()
        return path

    def new_path(self):
        path = Path(
            f"content/part{self.part_num}/ch{self.ch_num}/sec{self.sec_num}.tex"
        )
        return path


curr_part = curr_ch = None

def modify_file(sth: Part | Chapter | Section):
    global curr_part, curr_ch
    if not sth.new_path().parent.exists():
        sth.new_path().parent.mkdir(parents=True, exist_ok=True)
    match sth:
        case Part(_):
            curr_part = sth
            content = f"\\part{{{sth.title}}}\n" + sth.old_path().read_text()
            sth.new_path().write_text(content)
        case Chapter(_):
            curr_ch = sth
            content = f"\\chapter{{{sth.title}}}\n" + sth.old_path().read_text()
            sth.new_path().write_text(content)
            with curr_part.new_path().open("a") as f:
                f.write(f"\n\\subfile{{part{sth.part_num}/ch{sth.ch_num}.tex}}")
            if (sth.old_folder() / "images").exists():
                (sth.new_folder() / "images").mkdir(parents=True, exist_ok=True)
                for img in (sth.old_folder() / "images").iterdir():
                    shutil.copy(img, sth.new_folder() / "images")
        case Section(_):
            content = f"\\section{{{sth.title}}}\n" + sth.old_path().read_text()
            sth.new_path().write_text(content)
            with curr_ch.new_path().open("a") as f:
                f.write(f"\n\\subfile{{ch{sth.ch_num}/sec{sth.sec_num}.tex}}")


part_num = 0
def parse_toc(s: str):
    global part_num
    for line in s.splitlines():
        if "%" in line:
            continue
        # \section{Part II: 泛型代码中的移动语义}
        if "\\section" in line:
            title = line.split(":")[1].strip("}").strip()
            part_num += 1
            yield Part(part_num, title)
        # \subsection{13 只移动类型}
        if "\\subsection" in line:
            ch_num, title = line.split("{")[1].strip("}").split()
            yield Chapter(part_num, int(ch_num), title)
        if "\\subsubsection" in line:
        # \subsubsection{13.1 声明和使用只移动类型}
            ch_sec, title = line.split("{")[1].strip("}").split()
            ch_num, sec_num = ch_sec.split(".")
            yield Section(part_num, int(ch_num), int(sec_num), title)


if __name__ == "__main__":
    for part in parse_toc(Path("toc").read_text()):
        modify_file(part)
