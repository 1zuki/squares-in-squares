"""Parse public square-catalogue SVGs into high-precision candidate JSON."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import mpmath

mpmath.mp.dps = 70
XLINK = "{http://www.w3.org/1999/xlink}href"
NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
IDENTITY = tuple(mpmath.mpf(v) for v in (1, 0, 0, 1, 0, 0))


def number(value):
    return mpmath.mpf(value.strip())


def matmul(a, b):
    a0, a1, a2, a3, a4, a5 = a
    b0, b1, b2, b3, b4, b5 = b
    return (a0 * b0 + a2 * b1, a1 * b0 + a3 * b1, a0 * b2 + a2 * b3,
            a1 * b2 + a3 * b3, a0 * b4 + a2 * b5 + a4, a1 * b4 + a3 * b5 + a5)


def transform(value):
    matrix = IDENTITY
    for name, raw in re.findall(r"(\w+)\s*\(([^)]*)\)", value or ""):
        vals = [number(v) for v in re.findall(NUM, raw)]
        if name == "translate":
            t = (1, 0, 0, 1, vals[0], vals[1] if len(vals) > 1 else 0)
        elif name == "scale":
            t = (vals[0], 0, 0, vals[1] if len(vals) > 1 else vals[0], 0, 0)
        elif name == "rotate":
            angle = vals[0] * mpmath.pi / 180
            c, s = mpmath.cos(angle), mpmath.sin(angle)
            t = (c, s, -s, c, 0, 0)
            if len(vals) == 3:
                t = matmul(matmul((1, 0, 0, 1, vals[1], vals[2]), t), (1, 0, 0, 1, -vals[1], -vals[2]))
        elif name == "matrix":
            t = tuple(vals)
        else:
            raise ValueError(f"unsupported SVG transform {name}")
        matrix = matmul(matrix, tuple(mpmath.mpf(v) for v in t))
    return matrix


def parse_path(data):
    tokens = re.findall(rf"[MmLlHhVvZz]|{NUM}", data or "")
    polygons, current = [], []
    x = y = mpmath.mpf(0)
    command = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            if command in "Zz":
                if current:
                    polygons.append(current)
                    current = []
                continue
        if command in "Mm":
            nx, ny = number(tokens[index]), number(tokens[index + 1]); index += 2
            if command == "m": nx, ny = x + nx, y + ny
            if current: polygons.append(current)
            current = [(nx, ny)]; x, y = nx, ny
            command = "L" if command == "M" else "l"
        elif command in "Ll":
            nx, ny = number(tokens[index]), number(tokens[index + 1]); index += 2
            if command == "l": nx, ny = x + nx, y + ny
            x, y = nx, ny; current.append((x, y))
        elif command in "Hh":
            nx = number(tokens[index]); index += 1
            if command == "h": nx += x
            x = nx; current.append((x, y))
        elif command in "Vv":
            ny = number(tokens[index]); index += 1
            if command == "v": ny += y
            y = ny; current.append((x, y))
        else:
            raise ValueError(f"unsupported path command {command}")
    if current: polygons.append(current)
    return polygons


def inside(polygons, px, py):
    result = False
    for polygon in polygons:
        for index, (x1, y1) in enumerate(polygon):
            x2, y2 = polygon[(index + 1) % len(polygon)]
            if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
                result = not result
    return result


def path_cells(data):
    polygons = parse_path(data)
    try:
        return _path_cells(polygons)
    except ValueError:
        swapped = [[(y, x) for x, y in polygon] for polygon in polygons]
        return [(x, y) for y, x in _path_cells(swapped)]


def _path_cells(polygons):
    points = [point for polygon in polygons for point in polygon]
    xs = sorted(set(point[0] for point in points)); ys = sorted(set(point[1] for point in points))
    cells = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            if inside(polygons, (x0 + x1) / 2, (y0 + y1) / 2):
                if abs((x1 - x0) - mpmath.nint(x1 - x0)) > mpmath.mpf("1e-30") or abs((y1 - y0) - mpmath.nint(y1 - y0)) > mpmath.mpf("1e-30"):
                    raise ValueError("non-integral rectilinear path cell")
                for i in range(int(mpmath.nint(x1 - x0))):
                    for j in range(int(mpmath.nint(y1 - y0))):
                        cells.append((x0 + i, y0 + j))
    return cells


class Extractor:
    def __init__(self, root):
        self.ids = {element.get("id"): element for element in root.iter() if element.get("id")}
        self.squares = []

    def emit(self, matrix, i, j):
        a, b, c, d, e, f = matrix
        cx, cy = i + mpmath.mpf("0.5"), j + mpmath.mpf("0.5")
        self.squares.append((a * cx + c * cy + e, b * cx + d * cy + f, mpmath.atan2(b, a)))

    def walk(self, element, matrix):
        tag = element.tag.split("}")[-1]
        if tag in {"defs", "script", "title", "desc", "style", "text", "metadata"}:
            return
        style = (element.get("style") or "").replace(" ", "")
        if "fill:none" in style and tag != "g":
            return
        matrix = matmul(matrix, transform(element.get("transform")))
        if tag == "use":
            ref = (element.get(XLINK) or element.get("href") or "").lstrip("#")
            if ref == "outer": return
            matrix = matmul(matrix, (1, 0, 0, 1, number(element.get("x", "0")), number(element.get("y", "0"))))
            self.walk(self.ids[ref], matrix)
        elif tag == "rect":
            width, height = number(element.get("width")), number(element.get("height"))
            if element.get("id") == "outer": return
            if width != mpmath.nint(width) or height != mpmath.nint(height): raise ValueError("non-integral rect")
            matrix = matmul(matrix, (1, 0, 0, 1, number(element.get("x", "0")), number(element.get("y", "0"))))
            for i in range(int(width)):
                for j in range(int(height)):
                    self.emit(matrix, i, j)
        elif tag == "path":
            for i, j in path_cells(element.get("d")):
                self.emit(matrix, i, j)
        elif tag in {"g", "svg"}:
            for child in element:
                self.walk(child, matrix)


def parse(path: Path):
    root = ET.parse(path).getroot()
    viewbox = root.get("viewBox", "").split()
    if len(viewbox) != 4: raise ValueError("missing viewBox")
    side = number(viewbox[2])
    extractor = Extractor(root)
    extractor.walk(root, IDENTITY)
    return side, extractor.squares


def main(svg_dir: str, output: str):
    result, errors = {}, []
    for path in sorted(Path(svg_dir).glob("square-*.svg")):
        match = re.fullmatch(r"square-(\d+)", path.stem)
        if not match: continue
        n = int(match.group(1))
        if n > 1000:
            continue
        try:
            side, squares = parse(path)
            if len(squares) != n: raise ValueError(f"parsed {len(squares)} squares, expected {n}")
            current = result.get(str(n))
            if current is None or side < mpmath.mpf(current["side"]):
                result[str(n)] = {"source_file": path.name, "side": mpmath.nstr(side, 60), "squares": [[mpmath.nstr(v, 60) for v in s] for s in squares]}
        except Exception as exc:  # noqa: BLE001 - report every bad source
            errors.append(f"{path.name}: {exc}")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(result, indent=2) + "\n")
    print(f"parsed {len(result)} records; {len(errors)} errors")
    for error in errors: print(error)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
