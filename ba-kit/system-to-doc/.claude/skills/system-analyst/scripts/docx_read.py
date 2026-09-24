#!/usr/bin/env python3
"""Doc .docx bang zipfile + ElementTree — KHONG can python-docx.

Tra ve: paragraphs [(style, text)], tables [[[cell,...],...]], images [(name, cx_emu, cy_emu)]
"""
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
EMU_PER_INCH = 914400


def _text(el):
    return "".join(t.text or "" for t in el.iter(W + "t"))


def _style(p):
    pPr = p.find(W + "pPr")
    if pPr is None:
        return ""
    s = pPr.find(W + "pStyle")
    return s.get(W + "val") if s is not None else ""


class Docx:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.root = ET.fromstring(self.zip.read("word/document.xml"))
        self.body = self.root.find(W + "body")
        self.paragraphs = []
        self.tables = []
        self._walk(self.body)

    def _walk(self, node):
        for child in node:
            tag = child.tag.replace(W, "")
            if tag == "p":
                self.paragraphs.append((_style(child), _text(child).strip()))
            elif tag == "tbl":
                rows = []
                for r in child.findall(W + "tr"):
                    rows.append([_text(c).strip() for c in r.findall(W + "tc")])
                self.tables.append(rows)

    @property
    def all_text(self):
        parts = [t for _, t in self.paragraphs]
        for tb in self.tables:
            for r in tb:
                parts.extend(r)
        return "\n".join(parts)

    def headings(self):
        return [t for s, t in self.paragraphs if s.startswith("Heading") or s == "Title"]

    def images(self):
        out = []
        for ext in self.root.iter(A + "ext"):
            cx, cy = ext.get("cx"), ext.get("cy")
            if cx and cy:
                out.append((int(cx), int(cy)))
        media = [n for n in self.zip.namelist() if n.startswith("word/media/")]
        return media, out

    def content_width_emu(self):
        sect = self.body.find(W + "sectPr")
        if sect is None:
            return 6 * EMU_PER_INCH
        sz = sect.find(W + "pgSz")
        mar = sect.find(W + "pgMar")
        w = int(sz.get(W + "w")) if sz is not None else 12240
        left = int(mar.get(W + "left")) if mar is not None else 1440
        right = int(mar.get(W + "right")) if mar is not None else 1440
        return (w - left - right) * 635  # twip -> EMU
