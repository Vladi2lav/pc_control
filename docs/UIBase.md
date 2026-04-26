# UIBase.py — XML-to-PySide6 движок рендеринга

Преобразует XML-описание интерфейса в живые PySide6 виджеты.
Поддерживает dark-glass стилистику, кастомные компоненты, сигналы и анимации.

---

## XML-синтаксис

```xml
<Window title="Панель" width="400" height="300">
    <VBox spacing="8" padding="12">
        <Label text="Привет" style="title"/>
        <Button id="btn_close" text="✕ Закрыть" style="danger"/>
        <Input id="inp_name" placeholder="Введите имя..."/>
        <Spacer/>
        <HBox spacing="4">
            <Label text="Статус:" style="muted"/>
            <Label id="lbl_status" text="OK" style="accent"/>
        </HBox>
    </VBox>
</Window>
```

---

## Использование

```python
from components.UIBase import UIRenderer

renderer = UIRenderer()
widget, refs = renderer.load_file("modules/glass_panel/layout.xml")
# refs — dict {id: widget} для всех элементов с id="..."
refs["btn_close"].clicked.connect(my_handler)
```

---

## Поддерживаемые теги

| Тег          | Описание                                             |
|--------------|------------------------------------------------------|
| `Window`     | Корневой контейнер, VBox. Атрибуты: title, width, height |
| `VBox`       | Вертикальный лейаут. Атрибуты: spacing, padding      |
| `HBox`       | Горизонтальный лейаут. Атрибуты: spacing, padding    |
| `Panel`      | Аналог VBox, glass-контейнер                         |
| `Label`      | Текстовая метка. Атрибуты: text, style, align        |
| `Button`     | Кнопка. Атрибуты: text, style                        |
| `Input`      | Однострочное поле. Атрибуты: placeholder, text, style |
| `TextArea`   | Многострочное поле. Атрибуты: text, style            |
| `CheckBox`   | Чекбокс. Атрибуты: text, checked, style              |
| `ProgressBar`| Прогресс. Атрибуты: value, min, max                  |
| `Spacer`     | Растяжка (заполнитель пространства)                  |
| `Separator`  | Горизонтальная линия-разделитель                     |
| `Scroll`     | Прокручиваемая область. Атрибуты: spacing, padding   |
| `Stack`      | QStackedWidget для переключения страниц              |

---

## Общие атрибуты для всех тегов

| Атрибут      | Описание                                 |
|--------------|------------------------------------------|
| `id`         | Уникальный ID — попадает в dict refs     |
| `style`      | Стиль: `accent`, `danger`, `muted`, `title`, `close` |
| `tooltip`    | Всплывающая подсказка                    |
| `min_width`  | Минимальная ширина                       |
| `max_width`  | Максимальная ширина                      |
| `min_height` | Минимальная высота                       |
| `max_height` | Максимальная высота                      |
| `hidden`     | `true` — виджет скрыт при создании      |
| `disabled`   | `true` — виджет заблокирован            |
| `stretch`    | Вес растяжения в лейауте                |
| `align`      | Выравнивание: left, right, center, top, bottom |

---

## Стили (style=)

| Значение | Применение                         |
|----------|------------------------------------|
| `title`  | Крупный жирный белый текст (Label) |
| `muted`  | Приглушённый серый текст           |
| `accent` | Голубой акцентный цвет             |
| `danger` | Красный (предупреждение/удаление)  |
| `close`  | Кнопка-крестик (✕)                 |

---

## Классы компонентов

- **GlassLabel** — `QLabel` с glass-стилем
- **GlassButton** — `QPushButton` с glass-стилем и hover-анимацией
- **GlassInput** — `QLineEdit` с glass-стилем
- **GlassTextArea** — `QTextEdit` с glass-стилем
- **GlassCheckBox** — `QCheckBox` с glass-стилем
- **GlassProgressBar** — `QProgressBar` с gradient chunk
- **GlassSeparator** — горизонтальный `QFrame.HLine`
- **GlassPanel** — `QWidget` с property `glass="true"` (стекло)

---

## GLASS_STYLESHEET

Глобальная тема — тёмное стекло с акцентами.
Применяется автоматически к корневому виджету через `UIRenderer`.
Можно импортировать напрямую:

```python
from components.UIBase import GLASS_STYLESHEET
widget.setStyleSheet(GLASS_STYLESHEET)
```
