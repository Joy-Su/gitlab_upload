import jinja2
import markdown
from pathlib import Path
from shutil import copyfile, copytree
from datetime import datetime
from filelock import Timeout, FileLock
from pdf2image import convert_from_path
import urllib.request
import urllib.parse
import json


# https://github.com/yogeshwaran01/python-markdown-maker/blob/master/python_markdown_maker/__init__.py
def markdown_to_html(text: str) -> str:
    """ Function convert markdown to HTML """
    data = json.dumps({"text": text})
    data = data.encode()
    headers = {"Accept": "application/vnd.github.v3+json"}
    req = urllib.request.Request(
        url="https://api.github.com/markdown", data=data, headers=headers
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data) as response:
        text = response.read()
    return text.decode()


def headers(text: str, level: int) -> str:
    return level * "#" + f" {text}" + "\n"


def lists(list_item: list, k=0) -> str:
    code = list_item[0]
    struture = ""
    if code == "order":
        list_item = list_item[1:]
        count = 0
        for i in list_item:
            if isinstance(i, list):
                struture = struture + lists(i, k=k + 1)
            else:
                count = count + 1
                struture = struture + k * "\t" + str(count) + ". " + i + "\n"
        return struture
    else:
        for i in list_item:
            if isinstance(i, list):
                struture = struture + lists(i, k=k + 1)
            else:
                struture = struture + k * "\t" + "* " + i + "\n"
        return struture


def image(src: str, alt: str) -> str:

    return f"![{alt}]({src})" + "\n"


def links(link: str, text: str) -> str:

    return f"[{text}]({link})"


def styled_text(text: str, bold=False, italic=False, strikethrough=False):
    if bold:
        return f"**{text}**"
    if italic:
        return f"*{text}*"
    if strikethrough:
        return f"~~{text}~~"
    else:
        return text


def inline_code(text: str) -> str:
    return f"`{text}`"


def code_block(code: str, lang: str):
    return f"""```{lang}
    {code}
```\n"""


def blockquotes(text: str):
    return f"> {text} \n"


def task(text: str, checked: bool):
    if checked:
        return f"[x] {text}"
    return f"[ ] {text}"


class Table:
    def __init__(self, filednames):
        self.filednames = filednames
        self.all_items = []

    def add_item(self, item: list):
        self.all_items.append(item)

    def render(self):
        code = " | ".join(self.filednames) + "\n"
        line = " | ".join(
            [j * "-" for j in [len(i) for i in self.filednames]]
        ) + "\n"
        items = []
        for i in self.all_items:
            items.append(" | ".join(i))
        self.strcture = code + line + "\n".join(items)

        return self.strcture + "\n"


def collapsible(text: str, summary: str):
    return (
        f"""
<details>
  <summary>{summary}</summary>
{text}
</details>
"""
        + "\n"
    )


def aligned_header(text: str, level: int, align: str) -> str:
    return f"<h{level} align='{align}'>{text}</h{level}>" + "\n" + "\n"


def aligned_text(text: str, align: str) -> str:
    return f'<p align="{align}">{text}</p>'


def aligned_image(src: str, alt: str, align: str) -> str:
    return f'<p align="{align}"> <img alt="{align}" src="{src}"/> </p>' + "\n" + "\n"


class _render:
    def __init__(self, text):
        self.text = text

    def to_html(self):
        return markdown_to_html(self.text)

    def save_as_md(self, fp):
        fp.write(self.text)

    def save_as_html(self, fp):
        fp.write(self.to_html())


class Document:
    def __init__(self):
        self.document = ""

    @property
    def render(self):
        render_obj = _render(self.document)
        return render_obj

    def write(self, elements: list):
        self.document = "".join(elements)


TEMPLATE = """<!DOCTYPE html>
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<head>
    <link href="http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.0/css/bootstrap-combined.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
        }
        code, pre {
            font-family: monospace;
        }
        h1 code,
        h2 code,
        h3 code,
        h4 code,
        h5 code,
        h6 code {
            font-size: inherit;
        }
        #searchbar{
            margin-left: 15%;
            padding:15px;
            border-radius: 10px;
        }
        input[type=text] {
            width: 30%;
            -webkit-transition: width 0.15s ease-in-out;
            transition: width 0.15s ease-in-out;
        }
        input[type=text]:focus {
            width: 70%;
        }
        li {
            margin: 15px 0;
        }
        .project {
            margin-left: 15%;
        }
    </style>
    <script type="text/javascript">
        function search_project() {
            let input = document.getElementById('searchbar').value
            input=input.toLowerCase();
            let x = document.getElementsByClassName('project');
            for (i = 0; i < x.length; i++) {
                if (!x[i].innerHTML.toLowerCase().includes(input)) {
                    x[i].style.display="none";
                }
                else {
                    x[i].style.display="";
                }
            }
        }
    </script>
</head>
<body>
{{content}}
</body>
</html>
"""


class Record:
    def __init__(self, name: str, keyword: list, summary: str, url: str,
                 img: list, mail: str, path: str, backup: list, bkprefix: str):
        """
        name:     名称 [str]
        keyword:  关键词 [list]
        summary:  描述 [str]
        url:      gitlab 地址 [str]
        img:      图片路径 [list]
        mail:     上传人员 [str]
        path:     输出目录 [str]
        backup:   备份文件 [list]
        pkprefix: 备份目录 [str]
        """
        self.name = name
        self.keyword = keyword
        self.summary = summary
        self.url = url
        self.img = img
        self.mail = mail
        self.path = path
        self.backup = backup
        self.bkprefix = bkprefix
        self.doc = None

    def repo_html(self):
        """生成图片预览网页"""
        rpath = Path(self.path, self.name)
        try:
            Path.mkdir(rpath, parents=True, exist_ok=False)
            rpath.chmod(0o777)
        except OSError as e:
            print(e)
            raise

        img_rel = []
        for file in self.img:
            source = Path(file)
            if source.suffix in ['.png', '.pdf']:
                target = Path(self.path, self.name, source.stem + '.png')
                img_rel.append(source.stem + '.png')
                if source.suffix == '.png':
                    try:
                        copyfile(file, str(target))
                    except IOError as e:
                        print(e)
                        raise
                elif source.suffix == '.pdf':
                    try:
                        page = convert_from_path(file, 72)
                        page[0].save(str(target), 'PNG')
                    except OSError as e:
                        print(e)
                        raise
                target.chmod(0o666)
            else:
                print(f"Unknown image suffix, skipping {file}")

        if len(self.backup) > 0:
            bpath = Path(self.bkprefix, self.name)
            Path.mkdir(bpath, parents=True, exist_ok=False)
            dirs = ['input', 'output', 'scripts']
            for idx in range(3):
                source = Path(self.backup[idx])
                target = Path(bpath, dirs[idx])
                try:
                    copytree(self.backup[idx], str(target))
                except IOError as e:
                    print(e)
                    raise

        ttl = headers(self.name, level=2)
        des = self.summary + '\n\n'
        url = links(self.url, self.url) + '\n\n'
        img = '\n'.join([image('./' + i, '') for i in img_rel])

        md = Document()
        md.write(ttl + des + url + img)

        extensions = ['extra', 'smarty']
        html = markdown.markdown(md.render.text,
                                 extensions=extensions,
                                 output_format='html5').replace(
                                     '<h2>',
                                     '<div class="project"><h2>').replace(
                                         '</ul>', '</ul></div>')
        self.doc = jinja2.Template(TEMPLATE).render(content=html)

        viewhtml = Path(self.path, self.name, 'view.html')
        with open(str(viewhtml), 'w') as file:
            file.write(self.doc)
        viewhtml.chmod(0o666)

    def index_html(self):
        """添加上传记录"""
        ttl = headers(self.name, level=2)
        des = self.summary + '\n\n'
        url = '仓库: ' + links(self.url, self.url)
        kwd = '关键词: ' + ', '.join([inline_code(i) for i in self.keyword])
        au = '上传人员: ' + self.mail
        vw = '预览: ' + links(f'./{self.name}/view.html', '图片预览')
        tm = '记录时间: ' + styled_text(str(datetime.now()), italic=True)

        md = Document()
        if len(self.img) == 0:
            md.write(ttl + des + lists([tm, au, url, kwd]))
        else:
            md.write(ttl + des + lists([tm, au, url, kwd, vw]))

        def write_file(flag, index_path, lock_path, doc, mode):
            lock = FileLock(str(lock_path), timeout=1)
            try:
                with lock.acquire(timeout=10):
                    with open(str(index_path), mode) as file:
                        file.write(doc)
            except Timeout:
                print(
                    "Another instance of this application currently holds the lock."
                )
            if not flag:
                index_path.chmod(0o666)
                lock_path.chmod(0o777)

        index_path_ = Path(self.path, 'index.md')
        lock_path_ = Path(self.path, 'index.md.lock')
        flag_ = index_path_.exists()
        write_file(flag_, index_path_, lock_path_, md.render.text + '\n<br/>\n', 'a+')

        with open(str(index_path_), 'r') as file:
            text = file.read()
        extensions = ['extra', 'smarty']
        html = markdown.markdown(text,
                                 extensions=extensions,
                                 output_format='html5').replace(
                                     '<h2>',
                                     '<div class="project"><h2>').replace(
                                         '</ul>', '</ul></div>')
        sb = '<input id="searchbar" onkeyup="search_project()" type="text" name="search" placeholder="筛选...">'
        self.doc = jinja2.Template(TEMPLATE).render(content=sb + '\n' + html)

        index_path = Path(self.path, 'index.html')
        lock_path = Path(self.path, 'index.html.lock')
        flag = index_path.exists()
        write_file(flag, index_path, lock_path, self.doc, 'w')
