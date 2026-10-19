"""Los 30 murales mitologicos de las Ruinas: 5 mundos x 6 criaturas. Une los cinco modulos arte_mitos_1..5."""
import arte_mitos_1 as _m1
import arte_mitos_2 as _m2
import arte_mitos_3 as _m3
import arte_mitos_4 as _m4
import arte_mitos_5 as _m5

_MODS = (_m1, _m2, _m3, _m4, _m5)
NOMBRES = [n for m in _MODS for n in m.NOMBRES]
MOTIVOS = [f for m in _MODS for f in m.MOTIVOS]
assert len(NOMBRES) == len(MOTIVOS) == 30
