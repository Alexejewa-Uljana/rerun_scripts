# scene_traj_rerun

Сцены и траектории описываются в JSON; скрипты склеивают, проверяют и отрисовывают их в
Rerun. Сцена и траектории — отдельные файлы: сцену не трогаем, меняем только траектории.

## Формат JSON

### scene — сцена
```json
{
  "format": "scene",          // тип документа
  "version": 1,
  "cell_size": 1.0,           // размер клетки мира
  "up": "z",                  // вертикальная ось
  "objects": [                // список статических объектов сцены
    {"type": "ground", "n": 49, "color": [92,132,92]},
    {"type": "border", "n": 49, "color": [140,190,140]},
    {"type": "building", "x": 26, "y": 24, "w": 5, "d": 5, "h": 16, "color": [195,198,205], "detail": true},
    {"type": "box", "center": [x,y,z], "size": [w,d,h], "color": [150,155,170]},
    {"type": "mesh", "vertices": [[...]], "faces": [[...]], "color": [150,150,200]},
    {"type": "occupancy", "grid": [[0,1],[1,1]], "origin": [0,0,0], "cell": 1.0, "color": [150,155,170]}
  ]
}
```
Поля объектов:
- `ground` — сплошная земля размера `n`; `color` — цвет.
- `border` — рамка-периметр из кубиков размера `n` (для масштаба); `color` — цвет.
- `building` — здание, вписанное в bounding box `w x d x h` с углом основания в `(x,y)`,
  низ от `z=0` до `z=h`. Силуэт сужается кверху (низ шире, верх уже), с окнами.
  `detail:false` рисует простой параллелепипед `w x d x h`.
- `box` — параллелепипед: `center` — центр, `size` — размеры `[w,d,h]`; `color` — цвет.
- `mesh` — произвольная треугольная сетка: `vertices`, `faces`; `color` — цвет.
- `occupancy` — сетка занятости: `grid` 2D `[H][W]` или 3D `[H][W][D]`, ненулевая клетка -> куб;
  `origin` — сдвиг, `cell` — размер клетки, `color` — цвет.

### trajectories — траектории
```json
{
  "format": "trajectories",   // тип документа
  "version": 1,
  "cell_size": 1.0,
  "angle_units": "rad",       // единицы углов: "rad" или "deg"
  "agents": [
    {"name": "red", "color": [220,70,60], "radius": 0.9, "body": "ball",
     "trajectory": [[t, x, y], [t, x, y]]},
    {"name": "plane", "color": [220,35,35], "radius": 1.6, "body": "plane",
     "trajectory": [[t, x, y, z], [t, x, y, z]]}
  ]
}
```
Поля агента:
- `name` — имя (путь сущности в Rerun).
- `color` — цвет тела и следа.
- `radius` — радиус **описанного шара**: шар рисуется этого радиуса, модель самолёта целиком
  вписана в шар этого радиуса (размах крыльев равен длине корпуса, крылья по центру).
- `body` — `ball` (шар) или `plane` (модель самолёта).
- `trajectory` — строки переменной ширины: `[t,x,y]`, `[t,x,y,z]`, `[t,x,y,z,yaw]` или
  `[t,x,y,z,roll,pitch,yaw]`; недостающее дополняется нулями. Для `plane` без углов ориентация
  считается из формы пути, с 7-широкими строками берутся заданные углы.

### scene_traj — склейка сцены и траекторий
```json
{
  "format": "scene_traj",     // тип документа
  "version": 1,
  "cell_size": 1.0,
  "angle_units": "rad",
  "scene": {"objects": [ ... ]},   // объекты как в scene
  "agents": [ ... ]                // агенты как в trajectories
}
```

## Структура репозитория

```
scene_traj_rerun/
├── rerunlib.py                общий код: загрузка JSON + логирование в Rerun
├── render.py                  отрисовать JSON в Rerun (spawn) или экспортировать .rrd
├── merge.py                   склеить scene.json + N траекторий -> scene_traj.json
├── densify.py                 линейно сгустить траектории до заданной частоты
├── validate.py                проверить JSON по схеме (по полю "format")
├── schema/
│   ├── scene.schema.json
│   ├── trajectories.schema.json
│   └── combined.schema.json
├── generators/                генераторы примеров (математика -> JSON)
│   ├── gen_arena_scene.py     сцена: рамка-периметр
│   ├── gen_occupancy_scene.py сцена: occupancy grid
│   ├── gen_city_scene.py      сцена: город (земля + здания)
│   ├── gen_city_plane.py      траектория: самолёт над/между зданиями
│   ├── gen_crossing.py        траектории: пересечение накрест
│   ├── gen_overtake.py        траектории: обгон по дуге
│   └── gen_speeds.py          траектории: параллельные прямые, разная скорость
├── examples/
│   ├── scenes/                arena.json, city.json, occupancy.json
│   ├── trajectories/          crossing.json, overtake.json, speeds.json, city_plane.json
│   ├── combined/              scene_traj.json (сцена + траектории)
│   └── rrd/                   экспортированные .rrd
└── requirements.txt
```

## Установка

```bash
pip install -r requirements.txt
```

## Как запускать

Сгенерировать примеры (пишет JSON в `examples/`):
```bash
python generators/gen_city_scene.py
python generators/gen_city_plane.py
```

Склеить сцену и траектории в один файл:
```bash
python merge.py --scene examples/scenes/city.json --traj examples/trajectories/city_plane.json \
  -o examples/combined/city.json
```

Проверить по схеме:
```bash
python validate.py examples/combined/city.json
```

Отрисовать в Rerun (открывает вьюер):
```bash
python render.py examples/combined/city.json
python render.py --scene examples/scenes/arena.json --traj examples/trajectories/crossing.json
python render.py examples/scenes/occupancy.json
```

Экспортировать `.rrd` и открыть без Python:
```bash
python render.py examples/combined/city.json --save examples/rrd/city.rrd
rerun examples/rrd/city.rrd
```

## Линейное сгущение (densify)

Если точек в траектории мало, движение в Rerun «скачет» (между метками времени Rerun не
интерполирует). Опция линейно вставляет промежуточные точки с заданной частотой; исходные
точки сохраняются, вставка идёт только там, где шаг по времени больше заданного.

Отдельным скриптом (переписывает JSON):
```bash
python densify.py examples/trajectories/crossing.json -o crossing_dense.json --fps 30
python densify.py examples/trajectories/crossing.json -o crossing_dense.json --dt 0.05
```

Флагом при рендере (исходный JSON не меняется):
```bash
python render.py examples/combined/city.json --fps 30
python render.py --scene examples/scenes/arena.json --traj traj.json --dt 0.05 --save out.rrd
```

`--fps` задаёт частоту (точки через `1/fps` секунды), `--dt` — шаг по времени напрямую.
Углы перед интерполяцией разворачиваются (`unwrap`), чтобы не было скачков на ±180°.
