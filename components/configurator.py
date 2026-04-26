import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QDockWidget, QMdiArea, QMdiSubWindow, QTabWidget, QLabel, QTextEdit, 
    QSplitter, QFrame, QPushButton, QLineEdit, QToolBar, QMenuBar, QMenu,
    QHeaderView, QListWidget, QStackedWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QFont, QColor, QPalette

class FormEditorWindow(QMdiSubWindow):
    def __init__(self, context_name):
        super().__init__()
        self.setWindowTitle(f"Обработка {context_name}: Форма")
        self.resize(800, 600)
        
        main_widget = QWidget()
        self.setWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        for icon in ["➕", "✏️", "❌", "⬆️", "⬇️", "🖥️", "🔍"]:
            act = QAction(icon, self)
            toolbar.addAction(act)
        main_layout.addWidget(toolbar)
        
        # Bottom tabs (Форма / Модуль)
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setTabPosition(QTabWidget.TabPosition.South)
        main_layout.addWidget(self.bottom_tabs)
        
        # --- ФОРМА TAB ---
        form_tab = QWidget()
        form_layout = QVBoxLayout(form_tab)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter_v = QSplitter(Qt.Orientation.Vertical)
        
        # Top half: Trees
        splitter_h = QSplitter(Qt.Orientation.Horizontal)
        
        # Left tree: Elements
        elements_widget = QWidget()
        el_layout = QVBoxLayout(elements_widget)
        el_layout.setContentsMargins(0,0,0,0)
        
        el_tree = QTreeWidget()
        el_tree.setHeaderHidden(True)
        root_el = QTreeWidgetItem(["Форма"])
        root_el.setExpanded(True)
        cmd_panel = QTreeWidgetItem(["Командная панель"])
        req1 = QTreeWidgetItem(["Реквизит1"])
        req1.setForeground(0, QColor(180, 50, 50))
        root_el.addChild(cmd_panel)
        root_el.addChild(req1)
        el_tree.addTopLevelItem(root_el)
        
        el_tabs = QTabWidget()
        el_tabs.setTabPosition(QTabWidget.TabPosition.South)
        el_tabs.addTab(el_tree, "Элементы")
        el_tabs.addTab(QWidget(), "Командный интерфейс")
        el_layout.addWidget(el_tabs)
        
        # Right tree: Requisites
        req_widget = QWidget()
        req_layout = QVBoxLayout(req_widget)
        req_layout.setContentsMargins(0,0,0,0)
        
        req_tree = QTreeWidget()
        req_tree.setHeaderLabels(["Реквизит", "Использовать", "Тип"])
        req_tree.setColumnWidth(0, 150)
        req_tree.setColumnWidth(1, 80)
        
        root_obj = QTreeWidgetItem(["Объект", "", "(Обработка)"])
        root_obj.setExpanded(True)
        sub_req = QTreeWidgetItem(["Реквизит1", "☑", "Строка"])
        root_obj.addChild(sub_req)
        req_tree.addTopLevelItem(root_obj)
        
        req_tabs = QTabWidget()
        req_tabs.setTabPosition(QTabWidget.TabPosition.South)
        req_tabs.addTab(req_tree, "Реквизиты")
        req_tabs.addTab(QWidget(), "Команды")
        req_tabs.addTab(QWidget(), "Параметры")
        req_layout.addWidget(req_tabs)
        
        splitter_h.addWidget(elements_widget)
        splitter_h.addWidget(req_widget)
        
        # Bottom half: Visual Preview
        preview_frame = QFrame()
        preview_frame.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc;")
        preview_layout = QVBoxLayout(preview_frame)
        
        dummy_form = QFrame()
        dummy_form.setStyleSheet("background: white; border: 1px solid #999;")
        dummy_form.setFixedSize(300, 150)
        df_layout = QVBoxLayout(dummy_form)
        
        btn_more = QPushButton("Еще ▾")
        btn_more.setFixedWidth(60)
        df_layout.addWidget(btn_more, alignment=Qt.AlignmentFlag.AlignRight)
        
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Реквизит1:"))
        input_row.addWidget(QLineEdit())
        df_layout.addLayout(input_row)
        df_layout.addStretch()
        
        preview_layout.addWidget(dummy_form, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        splitter_v.addWidget(splitter_h)
        splitter_v.addWidget(preview_frame)
        form_layout.addWidget(splitter_v)
        
        # --- МОДУЛЬ TAB ---
        module_tab = QWidget()
        mod_layout = QVBoxLayout(module_tab)
        mod_layout.setContentsMargins(0,0,0,0)
        code_edit = QTextEdit()
        code_edit.setFont(QFont("Consolas", 10))
        code_edit.setText("// Модуль формы\n\nПроцедура ПриОтображении()\n\t// Код здесь\nКонецПроцедуры\n")
        mod_layout.addWidget(code_edit)
        
        self.bottom_tabs.addTab(form_tab, "Форма")
        self.bottom_tabs.addTab(module_tab, "Модуль")

class ModuleMainWindow(QMdiSubWindow):
    def __init__(self, context_name):
        super().__init__()
        self.setWindowTitle(f"Обработка {context_name}")
        self.resize(600, 400)
        
        main_widget = QWidget()
        self.setWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # Left tabs (ListWidget)
        self.list_tabs = QListWidget()
        self.list_tabs.setFixedWidth(150)
        tabs = ["Основные", "Подсистемы", "Функциональные опции", "Данные", "Формы", "Команды", "Макеты", "Права", "Прочее"]
        self.list_tabs.addItems(tabs)
        layout.addWidget(self.list_tabs)
        
        # Right content
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Create pages for each tab (we mainly care about "Формы")
        for tab in tabs:
            page = QWidget()
            pl = QVBoxLayout(page)
            if tab == "Формы":
                pl.addWidget(QLabel("Форма обработки: [ Форма ... 🔍 ]"))
                
                tb = QToolBar()
                for icon in ["➕", "✏️", "❌", "⬆️", "⬇️", "🗂️"]:
                    tb.addAction(QAction(icon, self))
                pl.addWidget(tb)
                
                forms_tree = QTreeWidget()
                forms_tree.setHeaderHidden(True)
                root = QTreeWidgetItem(["Формы"])
                root.setExpanded(True)
                f1 = QTreeWidgetItem(["Форма"])
                f1.setBackground(0, QColor(200, 220, 255))
                root.addChild(f1)
                forms_tree.addTopLevelItem(root)
                pl.addWidget(forms_tree)
            else:
                pl.addWidget(QLabel(f"Страница: {tab}"))
            self.stack.addWidget(page)
        
        self.list_tabs.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.list_tabs.setCurrentRow(4) # Select "Формы" by default

class ConfiguratorWindow(QMainWindow):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self._current_context = None
        self.setWindowTitle("Конфигуратор - Конфигурация")
        self.resize(1200, 800)
        
        self._setup_menubar()
        self._setup_toolbar()
        
        # MDI Area (Central)
        self.mdi = QMdiArea()
        self.mdi.setBackground(QColor(230, 230, 230))
        self.setCentralWidget(self.mdi)
        
        # Left Dock: Configuration Tree
        self.dock_config = QDockWidget("Конфигурация", self)
        self.dock_config.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.tree_config = QTreeWidget()
        self.tree_config.setHeaderHidden(True)
        self.tree_config.itemDoubleClicked.connect(self._on_tree_double_click)
        self.dock_config.setWidget(self.tree_config)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_config)
        
        # Right Dock: Properties
        self.dock_props = QDockWidget("Свойства: Поле", self)
        self.dock_props.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.tree_props = QTreeWidget()
        self.tree_props.setHeaderLabels(["Свойство", "Значение"])
        self.tree_props.setColumnWidth(0, 150)
        self._populate_properties()
        self.dock_props.setWidget(self.tree_props)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_props)

    def _setup_menubar(self):
        menubar = self.menuBar()
        for menu_name in ["Файл", "Правка", "Конфигурация", "Отладка", "Администрирование", "Сервис", "Окна", "Справка"]:
            menubar.addMenu(menu_name)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        icons = ["📄", "📁", "💾", "✖", "↩", "↪", "🔍", "▶", "🐞"]
        for icon in icons:
            toolbar.addAction(QAction(icon, self))

    def _populate_properties(self):
        # 1C style properties
        root_main = QTreeWidgetItem(["Основные"])
        root_main.setExpanded(True)
        root_main.addChild(QTreeWidgetItem(["Имя", "Реквизит1"]))
        root_main.addChild(QTreeWidgetItem(["Вид", "Поле ввода"]))
        root_main.addChild(QTreeWidgetItem(["ПутьКДанным", "Объект.Реквизит1"]))
        root_main.addChild(QTreeWidgetItem(["Видимость", "☑"]))
        
        root_use = QTreeWidgetItem(["Использование"])
        root_use.setExpanded(True)
        root_use.addChild(QTreeWidgetItem(["ТолькоПросмотр", "☐"]))
        root_use.addChild(QTreeWidgetItem(["МногострочныйРежим", "Авто"]))
        
        self.tree_props.addTopLevelItem(root_main)
        self.tree_props.addTopLevelItem(root_use)

    def open_context(self, context: str) -> None:
        self._current_context = context or "app"
        self._rebuild_tree()
        self.show()
        self.raise_()
        self.activateWindow()

    def _rebuild_tree(self):
        self.tree_config.clear()
        
        root = QTreeWidgetItem(["Конфигурация"])
        root.setIcon(0, QIcon()) # Empty for now
        root.setExpanded(True)
        
        root.addChild(QTreeWidgetItem(["Общие"]))
        root.addChild(QTreeWidgetItem(["Константы"]))
        root.addChild(QTreeWidgetItem(["Справочники"]))
        root.addChild(QTreeWidgetItem(["Документы"]))
        
        node_proc = QTreeWidgetItem(["Обработки"])
        node_proc.setExpanded(True)
        
        if self._current_context:
            node_mod = QTreeWidgetItem([self._current_context])
            node_mod.setExpanded(True)
            
            node_req = QTreeWidgetItem(["Реквизиты"])
            node_req.addChild(QTreeWidgetItem(["Реквизит1"]))
            node_mod.addChild(node_req)
            
            node_mod.addChild(QTreeWidgetItem(["Табличные части"]))
            
            node_forms = QTreeWidgetItem(["Формы"])
            node_forms.setExpanded(True)
            f1 = QTreeWidgetItem(["Форма"])
            f1.setData(0, Qt.ItemDataRole.UserRole, "form")
            node_forms.addChild(f1)
            node_mod.addChild(node_forms)
            
            node_mod.addChild(QTreeWidgetItem(["Команды"]))
            node_mod.addChild(QTreeWidgetItem(["Макеты"]))
            
            node_proc.addChild(node_mod)
        
        root.addChild(node_proc)
        self.tree_config.addTopLevelItem(root)

    def _on_tree_double_click(self, item, column):
        text = item.text(0)
        user_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if text == self._current_context:
            win = ModuleMainWindow(self._current_context)
            self.mdi.addSubWindow(win)
            win.show()
        elif user_data == "form" or text == "Форма":
            win = FormEditorWindow(self._current_context)
            self.mdi.addSubWindow(win)
            win.show()
            win.resize(700, 500)
