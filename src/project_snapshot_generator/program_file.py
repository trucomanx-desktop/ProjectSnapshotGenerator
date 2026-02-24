#!/usr/bin/python3

import sys
import os
import signal
import subprocess

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QAction
)

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QDesktopServices

import project_snapshot_generator.about as about
import project_snapshot_generator.modules.configure as configure
from project_snapshot_generator.modules.resources import resource_path
from project_snapshot_generator.modules.wabout    import show_about_window

from project_snapshot_generator.modules.file_report import gerar_bundle_codigo

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
    "config.file.json"
)

DEFAULT_CONTENT = {
    "toolbar_configure": "Configure",
    "toolbar_configure_tooltip": "Open the configure Json file of program GUI",
    "toolbar_about": "About",
    "toolbar_about_tooltip": "About the program",
    "toolbar_coffee": "Coffee",
    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",

    "lbl_select_file": "Main file (.py)",
    "btn_select_file": "Select file",
    "btn_select_file_tooltip": "Select the *.py file",
    
    "lbl_base_directory": "Base directory",
    "btn_select_directory": "Select directory",
    "btn_select_directory_tooltip": "Select the base directory",

    "btn_generate_snapshot": "Generate snapshot",
    "btn_generate_snapshot_tooltip": "Select the output txt file and generate a snapshot.",

    "snapshot_txt": "snapshot.txt",
    "msg_save_snapshot": "Save snapshot",
    "msg_select_file": "Select the file",
    "msg_select_directory": "Select the base directory",
    "msg_directory_not_exists": "Selected directory does not exist!",
    "msg_file_not_exists": "Selected directory does not exist!",
    "msg_success": "File successfully generated!",
    "msg_error": "Error generating file:",

    "window_width": 800,
    "window_height": 300
}

configure.verify_default_config(CONFIG_PATH, default_content=DEFAULT_CONTENT)
CONFIG = configure.load_config(CONFIG_PATH)
# ---------------------------------------

class SnapshotMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(about.__program_file_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])

        self.icon_path = resource_path("icons", "logo.png")
        self.setWindowIcon(QIcon(self.icon_path))
        
        self._create_toolbar()
        self._setup_ui()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _setup_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ---- Arquivo principal ----
        lbl_file = QLabel(CONFIG["lbl_select_file"])
        self.input_file = QLineEdit()
        self.input_file.setPlaceholderText(CONFIG["btn_select_file_tooltip"])

        btn_file = QPushButton(CONFIG["btn_select_file"])
        btn_file.setIcon(QIcon.fromTheme("text-x-generic"))
        btn_file.setToolTip(CONFIG["btn_select_file_tooltip"])
        btn_file.clicked.connect(self.select_file)

        layout_file = QHBoxLayout()
        layout_file.addWidget(self.input_file)
        layout_file.addWidget(btn_file)

        # ---- Diretório base ----
        lbl_dir = QLabel(CONFIG["lbl_base_directory"])
        self.input_dir = QLineEdit()
        self.input_dir.setPlaceholderText(CONFIG["btn_select_directory_tooltip"])

        btn_dir = QPushButton(CONFIG["btn_select_directory"])
        btn_dir.setIcon(QIcon.fromTheme("folder"))
        btn_dir.setToolTip(CONFIG["btn_select_directory_tooltip"])
        btn_dir.clicked.connect(self.select_directory)

        layout_dir = QHBoxLayout()
        layout_dir.addWidget(self.input_dir)
        layout_dir.addWidget(btn_dir)

        # ---- Separador ----
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        # ---- Botão gerar ----
        self.btn_generate = QPushButton(CONFIG["btn_generate_snapshot"])
        self.btn_generate.setToolTip(CONFIG["btn_generate_snapshot_tooltip"])
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.clicked.connect(self.generate_snapshot)

        # ---- Estética básica ----
        self.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 6px;
                background-color: #2c7be5;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a68d1;
            }
        """)

        # ---- Montagem ----
        main_layout.addWidget(lbl_file)
        main_layout.addLayout(layout_file)

        main_layout.addWidget(lbl_dir)
        main_layout.addLayout(layout_dir)

        main_layout.addWidget(separator)
        main_layout.addWidget(self.btn_generate, alignment=Qt.AlignCenter)

        central.setLayout(main_layout)

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
        
    # -------------------------------------------------
    # Ações
    # -------------------------------------------------
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            CONFIG["msg_select_file"],
            "",
            "Python Files (*.py)"
        )

        if file_path:
            self.input_file.setText(file_path)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            CONFIG["msg_select_directory"]
        )

        if directory:
            self.input_dir.setText(directory)

    def generate_snapshot(self):

        arquivo = self.input_file.text().strip()
        diretorio = self.input_dir.text().strip()

        if not os.path.isfile(arquivo):
            QMessageBox.warning(self, "Erro", CONFIG["msg_file_not_exists"])
            return

        if not os.path.isdir(diretorio):
            QMessageBox.warning(self, "Erro", CONFIG["msg_directory_not_exists"])
            return

        try:
            bundle = gerar_bundle_codigo(arquivo, diretorio)

            save_path, _ = QFileDialog.getSaveFileName(
                self,
                CONFIG["msg_save_snapshot"],
                CONFIG["snapshot_txt"],
                "Text Files (*.txt)"
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(bundle)

                QMessageBox.information(
                    self,
                    "Sucesso",
                    CONFIG["msg_success"]
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                CONFIG["msg_error"],
                str(e)
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
            "program_name": about.__program_file_name__,
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

# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_file_name__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_file_name__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_file_name__)
            return
    
    app = QApplication(sys.argv)
    app.setApplicationName(about.__program_file_name__)
    
    window = SnapshotMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
