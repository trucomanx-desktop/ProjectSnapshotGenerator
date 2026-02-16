import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QListWidget, QCheckBox,
    QFileDialog, QMessageBox, QGroupBox, QListWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

# Importar as funções do módulo project_report
from project_snapshot_generator.modules.project_report import generate_tree, serialize_project


class ProjectSerializerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Project Serializer')
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # === SEÇÃO 1: Seleção de Path ===
        path_group = QGroupBox("Diretório do Projeto")
        path_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Selecione o diretório do projeto...")
        path_layout.addWidget(self.path_input)
        
        self.btn_browse = QPushButton("Buscar...")
        self.btn_browse.setIcon(QIcon.fromTheme("folder"))
        self.btn_browse.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.btn_browse)
        
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)
        
        # === SEÇÃO 2: Filtros ===
        filter_group = QGroupBox("Filtros de Arquivos")
        filter_layout = QVBoxLayout()
        
        # Input para adicionar novos filtros
        add_filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Ex: *.py, *.js, *.md")
        self.filter_input.returnPressed.connect(self.add_filter)
        add_filter_layout.addWidget(self.filter_input)
        
        self.btn_add_filter = QPushButton("Adicionar")
        self.btn_add_filter.setIcon(QIcon.fromTheme("list-add"))
        self.btn_add_filter.clicked.connect(self.add_filter)
        add_filter_layout.addWidget(self.btn_add_filter)
        
        filter_layout.addLayout(add_filter_layout)
        
        # Lista de filtros
        self.filter_list = QListWidget()
        self.filter_list.setSelectionMode(QListWidget.MultiSelection)
        filter_layout.addWidget(self.filter_list)
        
        # Botão para remover filtros selecionados
        self.btn_remove_filter = QPushButton("Remover Selecionados")
        self.btn_remove_filter.setIcon(QIcon.fromTheme("list-remove"))
        self.btn_remove_filter.clicked.connect(self.remove_filters)
        filter_layout.addWidget(self.btn_remove_filter)
        
        # Adicionar filtros padrão
        default_filters = ["*.py", "*.json"]
        for f in default_filters:
            self.filter_list.addItem(f)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # === SEÇÃO 3: Opções ===
        options_group = QGroupBox("Opções")
        options_layout = QVBoxLayout()
        
        self.checkbox_full_content = QCheckBox("Incluir conteúdo completo dos arquivos")
        self.checkbox_full_content.setChecked(True)
        self.checkbox_full_content.stateChanged.connect(self.update_checkbox_text)
        options_layout.addWidget(self.checkbox_full_content)
        
        self.info_label = QLabel("✓ Será gerado: Estrutura de diretórios + Conteúdo dos arquivos")
        self.info_label.setStyleSheet("color: #2e7d32; font-style: italic;")
        options_layout.addWidget(self.info_label)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # === SEÇÃO 4: Diretórios a Ignorar ===
        ignore_group = QGroupBox("Diretórios a Ignorar (padrão)")
        ignore_layout = QVBoxLayout()
        
        ignore_label = QLabel("__pycache__, .git, venv, node_modules, .env, .venv")
        ignore_label.setStyleSheet("color: #666; font-style: italic;")
        ignore_layout.addWidget(ignore_label)
        
        ignore_group.setLayout(ignore_layout)
        main_layout.addWidget(ignore_group)
        
        # === SEÇÃO 5: Botão de Gerar ===
        self.btn_generate = QPushButton("Gerar Arquivo")
        self.btn_generate.setIcon(QIcon.fromTheme("document-save"))
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
    
    def update_checkbox_text(self):
        if self.checkbox_full_content.isChecked():
            self.info_label.setText("✓ Será gerado: Estrutura de diretórios + Conteúdo dos arquivos")
            self.info_label.setStyleSheet("color: #2e7d32; font-style: italic;")
        else:
            self.info_label.setText("✓ Será gerado: Apenas estrutura de diretórios")
            self.info_label.setStyleSheet("color: #f57c00; font-style: italic;")
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Selecione o Diretório do Projeto",
            str(Path.home())
        )
        if directory:
            self.path_input.setText(directory)
    
    def add_filter(self):
        filter_text = self.filter_input.text().strip()
        if filter_text:
            # Verifica se já existe
            existing_filters = [self.filter_list.item(i).text() 
                              for i in range(self.filter_list.count())]
            
            if filter_text not in existing_filters:
                self.filter_list.addItem(filter_text)
                self.filter_input.clear()
            else:
                QMessageBox.warning(self, "Aviso", f"O filtro '{filter_text}' já existe na lista!")
    
    def remove_filters(self):
        selected_items = self.filter_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos um filtro para remover!")
            return
        
        for item in selected_items:
            self.filter_list.takeItem(self.filter_list.row(item))
    
    def get_selected_filters(self):
        """Retorna lista de todos os filtros"""
        filters = []
        for i in range(self.filter_list.count()):
            filters.append(self.filter_list.item(i).text())
        return filters
    
    def generate_file(self):
        # Validações
        project_path = self.path_input.text().strip()
        if not project_path:
            QMessageBox.warning(self, "Erro", "Por favor, selecione um diretório!")
            return
        
        if not Path(project_path).exists():
            QMessageBox.critical(self, "Erro", "O diretório selecionado não existe!")
            return
        
        filters = self.get_selected_filters()
        if not filters:
            QMessageBox.warning(self, "Erro", "Adicione pelo menos um filtro!")
            return
        
        # Solicitar local para salvar
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Arquivo",
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
                output = generate_tree(project_path, filters)
            
            # Salvar arquivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"Arquivo gerado com sucesso!\n\n{output_file}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar arquivo:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    
    # Estilo global da aplicação
    app.setStyle('Fusion')
    
    
    window = ProjectSerializerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

