import os
import sys
import signal
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QListWidget, QCheckBox,
    QFileDialog, QMessageBox, QGroupBox, QSizePolicy, QAction
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QDesktopServices

import project_snapshot_generator.about as about
import project_snapshot_generator.modules.configure as configure
from project_snapshot_generator.modules.resources import resource_path
from project_snapshot_generator.modules.wabout import show_about_window

from project_snapshot_generator.modules.project_report import (
    generate_tree,
    serialize_project
)
from project_snapshot_generator.desktop import (
    create_desktop_file,
    create_desktop_directory,
    create_desktop_menu
)

# ---------- Path to config file ----------
CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    ".config",
    about.__package__,
    "config.json"
)

DEFAULT_CONTENT = {
    "toolbar_configure": "Configure",
    "toolbar_configure_tooltip": "Open the configure Json file of program GUI",
    "toolbar_about": "About",
    "toolbar_about_tooltip": "About the program",
    "toolbar_coffee": "Coffee",
    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",

    "group_project_dir": "Project Directory",
    "group_filters": "File Filters",
    "group_options": "Options",
    "group_ignore": "Ignored Directories (default)",

    "btn_browse": "Browse...",
    "btn_add_filter": "Add",
    "btn_remove_filter": "Remove Selected",
    "btn_generate": "Generate File",

    "tooltip_path_input": "Select the root directory of the project you want to serialize.",
    "tooltip_btn_browse": "Open a directory selection dialog.",
    "tooltip_filter_input": "Type a file pattern (example: *.py, *.json, *.md) and press Enter.",
    "tooltip_btn_add_filter": "Add the typed file pattern to the filter list.",
    "tooltip_filter_list": "List of file patterns that will be included in the snapshot.",
    "tooltip_btn_remove_filter": "Remove selected file patterns from the list.",
    "tooltip_checkbox_full_content": "If checked, full file contents will be included in the snapshot.",
    "tooltip_btn_generate": "Generate the final snapshot file using selected options.",

    "checkbox_full_content": "Include full file contents",

    "placeholder_path": "Select the project directory...",
    "placeholder_filter": "Example: *.py",

    "info_full": "✓ Will generate: Directory structure + File contents",
    "info_tree": "✓ Will generate: Directory structure only",

    "msg_select_directory": "Please select a directory!",
    "msg_directory_not_exists": "Selected directory does not exist!",
    "msg_add_filter": "Add at least one filter!",
    "msg_filter_exists": "Filter already exists!",
    "msg_remove_filter": "Select at least one filter to remove!",
    "msg_success": "File successfully generated!",
    "msg_error": "Error generating file:",

    "window_width": 800,
    "window_height": 600
}

configure.verify_default_config(CONFIG_PATH, default_content=DEFAULT_CONTENT)
CONFIG = configure.load_config(CONFIG_PATH)
# ---------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(about.__program_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])

        self.icon_path = resource_path("icons", "logo.png")
        self.setWindowIcon(QIcon(self.icon_path))

        self._create_toolbar()
        self._generate_ui()

    # ================= UI =================
    def _generate_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # === Project Directory ===
        path_group = QGroupBox(CONFIG["group_project_dir"])
        path_layout = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(CONFIG["placeholder_path"])
        self.path_input.setToolTip(CONFIG["tooltip_path_input"])
        path_layout.addWidget(self.path_input)

        self.btn_browse = QPushButton(CONFIG["btn_browse"])
        self.btn_browse.setIcon(QIcon.fromTheme("folder"))
        self.btn_browse.setToolTip(CONFIG["tooltip_btn_browse"])
        self.btn_browse.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.btn_browse)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # === Filters ===
        filter_group = QGroupBox(CONFIG["group_filters"])
        filter_layout = QVBoxLayout()

        add_filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(CONFIG["placeholder_filter"])
        self.filter_input.setToolTip(CONFIG["tooltip_filter_input"])
        self.filter_input.returnPressed.connect(self.add_filter)
        add_filter_layout.addWidget(self.filter_input)

        self.btn_add_filter = QPushButton(CONFIG["btn_add_filter"])
        self.btn_add_filter.setIcon(QIcon.fromTheme("list-add"))
        self.btn_add_filter.setToolTip(CONFIG["tooltip_btn_add_filter"])
        self.btn_add_filter.clicked.connect(self.add_filter)
        add_filter_layout.addWidget(self.btn_add_filter)

        filter_layout.addLayout(add_filter_layout)

        self.filter_list = QListWidget()
        self.filter_list.setToolTip(CONFIG["tooltip_filter_list"])
        filter_layout.addWidget(self.filter_list)

        self.btn_remove_filter = QPushButton(CONFIG["btn_remove_filter"])
        self.btn_remove_filter.setIcon(QIcon.fromTheme("list-remove"))
        self.btn_remove_filter.setToolTip(CONFIG["tooltip_btn_remove_filter"])
        self.btn_remove_filter.clicked.connect(self.remove_filters)
        filter_layout.addWidget(self.btn_remove_filter)

        for f in ["*.py", "*.json"]:
            self.filter_list.addItem(f)

        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # === Options ===
        options_group = QGroupBox(CONFIG["group_options"])
        options_layout = QVBoxLayout()

        self.checkbox_full_content = QCheckBox(CONFIG["checkbox_full_content"])
        self.checkbox_full_content.setChecked(True)
        self.checkbox_full_content.setToolTip(CONFIG["tooltip_checkbox_full_content"])
        self.checkbox_full_content.stateChanged.connect(self.update_info_label)
        options_layout.addWidget(self.checkbox_full_content)

        self.info_label = QLabel(CONFIG["info_full"])
        self.info_label.setStyleSheet("color: #2e7d32; font-style: italic;")
        options_layout.addWidget(self.info_label)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # === Ignored directories ===
        ignore_group = QGroupBox(CONFIG["group_ignore"])
        ignore_layout = QVBoxLayout()

        ignore_label = QLabel("__pycache__, .git, venv, node_modules, .env, .venv")
        ignore_label.setStyleSheet("color: #666; font-style: italic;")
        ignore_layout.addWidget(ignore_label)

        ignore_group.setLayout(ignore_layout)
        main_layout.addWidget(ignore_group)

        # === SEÇÃO 5: Botão de Gerar ===
        self.btn_generate = QPushButton(CONFIG["btn_generate"])
        self.btn_generate.setIcon(QIcon.fromTheme("document-save"))
        self.btn_generate.setToolTip(CONFIG["tooltip_btn_generate"])
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.btn_generate.clicked.connect(self.generate_file)
        main_layout.addWidget(self.btn_generate)

        # Estilo geral
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    # ================= Toolbar =================
    def _create_toolbar(self):
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.toolbar_spacer = QWidget()
        self.toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar.addWidget(self.toolbar_spacer)

        self.configure_action = QAction(
            QIcon.fromTheme("document-properties"),
            CONFIG["toolbar_configure"],
            self
        )
        self.configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        self.configure_action.triggered.connect(self.open_configure_editor)
        self.toolbar.addAction(self.configure_action)

        self.about_action = QAction(
            QIcon.fromTheme("help-about"),
            CONFIG["toolbar_about"],
            self
        )
        self.about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        self.about_action.triggered.connect(self.open_about)
        self.toolbar.addAction(self.about_action)

        self.coffee_action = QAction(
            QIcon.fromTheme("emblem-favorite"),
            CONFIG["toolbar_coffee"],
            self
        )
        self.coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        self.coffee_action.triggered.connect(self.on_coffee_action_click)
        self.toolbar.addAction(self.coffee_action)

    # ================= Logic =================
    def update_info_label(self):
        if self.checkbox_full_content.isChecked():
            self.info_label.setText(CONFIG["info_full"])
            self.info_label.setStyleSheet("color: #2e7d32; font-style: italic;")
        else:
            self.info_label.setText(CONFIG["info_tree"])
            self.info_label.setStyleSheet("color: #f57c00; font-style: italic;")

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            CONFIG["group_project_dir"],
            str(Path.home())
        )
        if directory:
            self.path_input.setText(directory)

    def add_filter(self):
        filter_text = self.filter_input.text().strip()
        if not filter_text:
            return

        existing = [
            self.filter_list.item(i).text()
            for i in range(self.filter_list.count())
        ]

        if filter_text in existing:
            QMessageBox.warning(self, "Warning", CONFIG["msg_filter_exists"])
            return

        self.filter_list.addItem(filter_text)
        self.filter_input.clear()

    def remove_filters(self):
        selected = self.filter_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", CONFIG["msg_remove_filter"])
            return

        for item in selected:
            self.filter_list.takeItem(self.filter_list.row(item))

    def get_selected_filters(self):
        return [
            self.filter_list.item(i).text()
            for i in range(self.filter_list.count())
        ]

    def generate_file(self):
        project_path = self.path_input.text().strip()

        if not project_path:
            QMessageBox.warning(self, "Error", CONFIG["msg_select_directory"])
            return

        if not Path(project_path).exists():
            QMessageBox.critical(self, "Error", CONFIG["msg_directory_not_exists"])
            return

        filters = self.get_selected_filters()
        if not filters:
            QMessageBox.warning(self, "Error", CONFIG["msg_add_filter"])
            return
        
        # Solicitar local para salvar
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            CONFIG["btn_generate"],
            str(Path.home() / "project_snapshot.txt"),
            "Text Files (*.txt);;All Files (*)"
        )

        if not output_file:
            return
        
        # Gerar o arquivo
        try:
            include_content = self.checkbox_full_content.isChecked()

            if include_content:
                # Usa a função importada do módulo project_report
                output = serialize_project(project_path, filters, incluir_tree=True)
            else:
                # Usa a função importada do módulo project_report (apenas estrutura)
                output = generate_tree( project_path, 
                                        filters, 
                                        ignorar = ['__pycache__', '.git', 'venv', 'node_modules', '.env', '.venv'])
            
            # Salvar arquivo
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)

            QMessageBox.information(self, "Success", CONFIG["msg_success"])

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"{CONFIG['msg_error']}\n{str(e)}"
            )

    # ================= Template Integrations =================
    def _open_file_in_text_editor(self, filepath):
        if os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', filepath])

    def open_configure_editor(self):
        self._open_file_in_text_editor(CONFIG_PATH)

    def open_about(self):
        data = {
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_name__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data, self.icon_path)

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_name__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
    

    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__)

    # Estilo global da aplicação
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

