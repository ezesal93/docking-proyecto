"""Genera Proyecto-2/bitacora.html a partir de los archivos reales del docking.

Uso, desde la raíz del repositorio:

    python -I herramientas/generar_bitacora_p2.py

Vuelve a leer los archivos de Proyecto-2 y reescribe la bitácora, así que
conviene ejecutarlo cada vez que se repita un acoplamiento o se agregue un
archivo. Los PDBQT son enormes: de cada uno se publican las primeras líneas y
el resto queda en un enlace a la versión raw de GitHub, que el navegador
muestra como texto plano.
"""

import re
import sys
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE = RAIZ / "Proyecto-2"
RAW = "https://raw.githubusercontent.com/ezesal93/docking-proyecto/main/Proyecto-2/"
LINEAS = 20

PROTEINAS = {"3ERT": "ERα", "3PP0": "HER2"}
LIGANDOS = ["tamoxifeno", "polygodial", "leptocarpina"]
NOMBRE = {"tamoxifeno": "Tamoxifeno", "polygodial": "Polygodial", "leptocarpina": "Leptocarpina"}


def leer(rel):
    return (BASE / rel).read_text(encoding="utf-8", errors="replace").rstrip("\n")


def enlace(rel):
    href = (RAW + rel) if rel.endswith(".pdbqt") else rel
    return f'<a href="{escape(href)}">{escape(rel)}</a>'


def bloque(rel, completo=False):
    """Un archivo: entero si es corto y de configuración, recortado si no."""
    lineas = leer(rel).splitlines()
    if completo or len(lineas) <= LINEAS:
        cuerpo, nota = "\n".join(lineas), f"Archivo: {enlace(rel)}"
    else:
        cuerpo = "\n".join(lineas[:LINEAS])
        nota = f"Se muestran {LINEAS} de {len(lineas)} líneas. Documento completo: {enlace(rel)}"
    return (f'<div class="doc"><h4>{escape(Path(rel).name)}</h4>'
            f"<pre>{escape(cuerpo)}</pre>"
            f'<p class="more">{nota}</p></div>')


def afinidad(rel):
    """La afinidad del modo 1 que Vina dejó en el registro."""
    m = re.search(r"^\s+1\s+(-?\d+\.?\d*)", leer(rel), re.M)
    return float(m.group(1)) if m else None


def coma(v, d=2):
    """Redondeo con el medio hacia arriba, para calzar con el informe escrito."""
    m = 10 ** d
    return f"{round(abs(v) * m + 1e-9) / m:.{d}f}".replace(".", ",")


def ruta_log(lig, p):
    carpeta = f"docking/docking-{p}/"
    nombre = f"{lig}-{p}-resultado{'' if (lig, p) == ('leptocarpina', '3ERT') else 's'}.txt"
    if (lig, p) == ("leptocarpina", "3ERT"):
        nombre = "leptocarina-3ERT-resultado.txt"   # así quedó escrito el archivo original
    return carpeta + nombre


def ruta_pose(lig, p):
    return (f"docking/docking-3ERT/{lig}-3ERTout.pdbqt" if p == "3ERT"
            else f"docking/docking-3PP0/{lig}-3PP0_out.pdbqt")


def ruta_config(lig, p):
    return f"docking/docking-{p}/{lig}-{p}config.txt"


def main():
    faltan = [r for r in
              [ruta_log(l, p) for l in LIGANDOS for p in PROTEINAS]
              + [ruta_pose(l, p) for l in LIGANDOS for p in PROTEINAS]
              + [ruta_config(l, p) for l in LIGANDOS for p in PROTEINAS]
              if not (BASE / r).exists()]
    if faltan:
        sys.exit("Faltan archivos:\n  " + "\n  ".join(faltan))

    # tabla resumen
    filas = []
    for lig in LIGANDOS:
        a = {p: afinidad(ruta_log(lig, p)) for p in PROTEINAS}
        d = a["3ERT"] - a["3PP0"]
        filas.append(f"<tr><td>{NOMBRE[lig]}</td>"
                     f'<td class="num">−{coma(a["3ERT"])}</td>'
                     f'<td class="num">−{coma(a["3PP0"])}</td>'
                     f'<td class="num">−{coma(d)}</td></tr>')

    redock = (f'<tr><td>4-hidroxitamoxifeno <span class="chico">(re-docking)</span></td>'
              f'<td class="num">−{coma(afinidad("oht.3ERT-redocking.txt"))}</td><td class="num">—</td><td class="num">—</td></tr>'
              f'<tr><td>Inhibidor 03Q <span class="chico">(re-docking)</span></td>'
              f'<td class="num">—</td><td class="num">−{coma(afinidad("03q-3PP0-redocking.txt"))}</td><td class="num">—</td></tr>')

    partes = {
        "prep_prot": "".join(bloque(f"docking/docking-{p}/" +
                                    ("3ERT_proteina.pdbqt" if p == "3ERT" else "3PP0_A.pdbqt"))
                             for p in PROTEINAS),
        "prep_lig": "".join(bloque(f"Ligandos/{l}.pdbqt") for l in LIGANDOS),
        "redock_cfg": bloque("3PP0/03q-3PP0config.txt", completo=True),
        "redock_log": (bloque("oht.3ERT-redocking.txt", completo=True)
                       + bloque("03q-3PP0-redocking.txt", completo=True)),
        "config": "".join(bloque(ruta_config(l, p), completo=True) for p in PROTEINAS for l in LIGANDOS),
        "logs": "".join(bloque(ruta_log(l, p), completo=True) for p in PROTEINAS for l in LIGANDOS),
        "poses": "".join(bloque(ruta_pose(l, p)) for p in PROTEINAS for l in LIGANDOS),
        "tabla": "".join(filas) + redock,
    }

    (BASE / "bitacora.html").write_text(PLANTILLA.format(**partes), encoding="utf-8")
    print("bitacora.html escrita:", len(LIGANDOS) * len(PROTEINAS), "acoplamientos")


PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a8456b' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='6' cy='7' r='2.2'/%3E%3Ccircle cx='18' cy='7' r='2.2'/%3E%3Ccircle cx='12' cy='17' r='2.2'/%3E%3Cpath d='M8 8l2.8 7M16 8l-2.8 7M8.2 7h7.6'/%3E%3C/svg%3E">
<title>Bitácora · Cáncer de mama y plantas nativas</title>
<style>
  body {{ font-family: Georgia, "Times New Roman", serif; color: #111; background: #fff;
         max-width: 820px; margin: 0 auto; padding: 24px 16px; line-height: 1.5; }}
  h1 {{ font-size: 1.7em; margin-bottom: 0; }}
  .sub {{ color: #555; margin-top: 4px; }}
  h2 {{ border-bottom: 2px solid #111; padding-bottom: 4px; margin-top: 2em; }}
  h3 {{ margin-top: 1.5em; }}
  h4 {{ margin: 0 0 4px; font-family: Consolas, monospace; font-size: .95em; }}
  .doc {{ margin: 14px 0 20px; break-inside: avoid; page-break-inside: avoid; }}
  pre {{ font-family: Consolas, "Courier New", monospace; font-size: 10.5px; line-height: 1.3;
         background: #f5f5f5; border: 1px solid #ccc; padding: 8px; margin: 0;
         white-space: pre; overflow-x: auto; }}
  .more {{ font-size: .85em; color: #444; margin: 4px 0 0; }}
  a {{ color: #0645ad; word-break: break-all; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
  th, td {{ border: 1px solid #999; padding: 4px 8px; text-align: left; }}
  td.num {{ text-align: right; font-family: Consolas, monospace; }}
  .chico {{ font-size: .82em; color: #555; }}
  .menu {{ position: sticky; top: 0; z-index: 10; display: flex; gap: 2px; overflow-x: auto;
           margin: -24px -16px 16px; padding: 8px 16px; background: #111;
           font-family: system-ui, sans-serif; font-size: .85em; white-space: nowrap; }}
  .menu a {{ color: #ddd; text-decoration: none; padding: 5px 10px; border-radius: 4px; word-break: normal; }}
  .menu a:hover {{ background: #333; color: #fff; }}
  .page {{ page-break-before: always; break-before: page; }}
  @media print {{
    body {{ max-width: none; padding: 0; }}
    .menu {{ display: none; }}
    pre {{ background: none; overflow: visible; white-space: pre-wrap; }}
    a {{ color: #111; text-decoration: none; }}
    h2, h3, h4 {{ break-after: avoid; page-break-after: avoid; }}
  }}
  @page {{ margin: 18mm 15mm; }}
</style>
</head>
<body>

<nav class="menu" aria-label="Secciones">
  <a href="index.html">← Recorrido</a>
  <a href="#obtencion">1. Obtención</a>
  <a href="#preparacion">2. Preparación</a>
  <a href="#validacion">3. Validación</a>
  <a href="#configuracion">4. Configuración</a>
  <a href="#resultados">5. Resultados</a>
</nav>

<h1>Bitácora de investigación: docking molecular</h1>
<p class="sub">Polygodial y leptocarpina frente al tamoxifeno, contra ERα (3ERT) y HER2 (3PP0) · AutoDock Vina 1.2.7</p>
<p class="sub">Emilia Antonia Cea Reyes · Escuela Particular N.º 95 Alemana, Paillaco</p>

<h2 id="obtencion">1. Obtención de las estructuras</h2>
<p>Las proteínas se descargaron del <strong>Protein Data Bank</strong>: la estructura <strong>3ERT</strong>,
que contiene ERα unido a 4-hidroxitamoxifeno, y la <strong>3PP0</strong>, de la que se usó la cadena A,
con el dominio quinasa de HER2 unido al inhibidor 03Q.</p>
<p>Los tres ligandos —tamoxifeno, polygodial y leptocarpina— se descargaron de <strong>PubChem</strong>
en formato <em>3D Conformer</em>. En PyMOL se eliminaron las aguas de las proteínas y se separó cada una
de su ligando cristalizado, que se guardó aparte para la validación.</p>

<h2 id="preparacion">2. Preparación de los archivos PDBQT</h2>
<p>En AutoDock Tools se agregaron los hidrógenos, se asignaron las cargas y los enlaces rotables, y todo
se guardó en formato PDBQT, que es el que exige Vina. Por su extensión, de cada archivo se muestran solo
las primeras líneas.</p>
<h3>2.1 Proteínas</h3>
{prep_prot}
<h3>2.2 Ligandos</h3>
{prep_lig}

<h2 id="validacion" class="page">3. Validación del protocolo por re-docking</h2>
<p>Antes de evaluar los compuestos de estudio se comprobó que el protocolo reprodujera la posición real
de un ligando conocido: se volvió a acoplar el ligando cristalizado de cada proteína y se superpuso en
PyMOL con el original.</p>
{redock_cfg}
{redock_log}

<h2 id="configuracion" class="page">4. Archivos de configuración</h2>
<p>Una caja de búsqueda por proteína, centrada sobre el ligando cristalizado, de 18,75 × 18,75 × 15 Å,
con espaciado 0,375 Å y exhaustiveness 32. Se muestran completos.</p>
{config}

<h2 id="resultados" class="page">5. Resultados del docking</h2>
<h3>5.1 Resumen: afinidad de la mejor pose</h3>
<table>
  <thead><tr><th>Ligando</th><th>ERα (3ERT)</th><th>HER2 (3PP0)</th><th>Δ</th></tr></thead>
  <tbody>{tabla}</tbody>
</table>
<p class="chico">Afinidades en kcal/mol, modo 1. Δ es la diferencia entre la afinidad por ERα y la
afinidad por HER2: un valor más negativo indica mayor preferencia por ERα.</p>

<h3>5.2 Registros de AutoDock Vina</h3>
{logs}

<h3 class="page">5.3 Poses generadas</h3>
<p>Las nueve poses de cada acoplamiento. Se muestran las primeras líneas; el documento completo está en
el enlace. Para verlas en 3D, el <a href="index.html">recorrido</a> tiene un visor interactivo.</p>
{poses}

</body>
</html>
"""

if __name__ == "__main__":
    main()
