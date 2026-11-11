import sys
import os
import img2pdf
from PyPDF2 import PdfMerger
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QListWidget, QFileDialog, QMessageBox, QHBoxLayout,
                             QTabWidget, QLabel)
from PyQt6.QtCore import Qt

# Kelas khusus untuk ListWidget agar mendukung Drag and Drop file dari luar
class DragDropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                # Filter ekstensi yang diizinkan (opsional)
                if file_path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    self.addItem(file_path)
        else:
            event.ignore()

class PDFToolbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Python PDF Toolbox - Drag & Drop Edition')
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_merger_tab(), "Merge PDF & Images")
        self.tabs.addTab(self.create_converter_tab(), "Bulk Image to PDF")

        self.main_layout.addWidget(self.tabs)
        self.setLayout(self.main_layout)

    def create_merger_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Tarik & Lepas (Drag & Drop) file dari folder ke sini:"))
        self.merge_list = DragDropListWidget() # Menggunakan class custom
        layout.addWidget(self.merge_list)

        nav_layout = QHBoxLayout()
        btn_up = QPushButton('▲ Atas')
        btn_down = QPushButton('▼ Bawah')
        btn_up.clicked.connect(lambda: self.move_item(self.merge_list, -1))
        btn_down.clicked.connect(lambda: self.move_item(self.merge_list, 1))
        nav_layout.addWidget(btn_up)
        nav_layout.addWidget(btn_down)
        layout.addLayout(nav_layout)

        ctrl_layout = QHBoxLayout()
        btn_add = QPushButton('➕ Tambah Manual')
        btn_remove = QPushButton('❌ Hapus Terpilih')
        btn_add.clicked.connect(lambda: self.add_files(self.merge_list, "Semua (*.pdf *.png *.jpg *.jpeg)"))
        btn_remove.clicked.connect(lambda: self.remove_selected(self.merge_list))
        ctrl_layout.addWidget(btn_add)
        ctrl_layout.addWidget(btn_remove)
        layout.addLayout(ctrl_layout)

        btn_run = QPushButton('PROSES PENGGABUNGAN')
        btn_run.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 15px;")
        btn_run.clicked.connect(self.process_merge)
        layout.addWidget(btn_run)

        widget.setLayout(layout)
        return widget

    def create_converter_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Tarik & Lepas gambar di sini untuk dikonversi:"))
        self.conv_list = DragDropListWidget()
        layout.addWidget(self.conv_list)

        ctrl_layout = QHBoxLayout()
        btn_add = QPushButton('➕ Tambah Manual')
        btn_clear = QPushButton('🗑️ Kosongkan')
        btn_add.clicked.connect(lambda: self.add_files(self.conv_list, "Images (*.png *.jpg *.jpeg)"))
        btn_clear.clicked.connect(self.conv_list.clear)
        ctrl_layout.addWidget(btn_add)
        ctrl_layout.addWidget(btn_clear)
        layout.addLayout(ctrl_layout)

        btn_run = QPushButton('KONVERSI MASSAL KE PDF')
        btn_run.setStyleSheet("background-color: #1565C0; color: white; font-weight: bold; padding: 15px;")
        btn_run.clicked.connect(self.process_conversion)
        layout.addWidget(btn_run)

        widget.setLayout(layout)
        return widget

    # --- UTILITIES ---
    def add_files(self, list_widget, file_filter):
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih File", "", file_filter)
        for f in files: list_widget.addItem(f)

    def remove_selected(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def move_item(self, list_widget, direction):
        curr_row = list_widget.currentRow()
        if curr_row == -1: return
        new_row = curr_row + direction
        if 0 <= new_row < list_widget.count():
            item = list_widget.takeItem(curr_row)
            list_widget.insertItem(new_row, item)
            list_widget.setCurrentRow(new_row)

    def process_merge(self):
        if self.merge_list.count() == 0: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil", "", "PDF Files (*.pdf)")
        if not save_path: return
        try:
            merger = PdfMerger()
            temps = []
            for i in range(self.merge_list.count()):
                path = self.merge_list.item(i).text()
                if path.lower().endswith('.pdf'):
                    merger.append(path)
                else:
                    temp_pdf = f"temp_m_{i}.pdf"
                    with open(temp_pdf, "wb") as f:
                        f.write(img2pdf.convert(path, rotation=img2pdf.Rotation.ifvalid))
                    merger.append(temp_pdf)
                    temps.append(temp_pdf)
            merger.write(save_path)
            merger.close()
            for t in temps: 
                if os.path.exists(t): os.remove(t)
            QMessageBox.information(self, "Berhasil", "File digabungkan!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def process_conversion(self):
        if self.conv_list.count() == 0: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan PDF", "", "PDF Files (*.pdf)")
        if not save_path: return
        try:
            img_paths = [self.conv_list.item(i).text() for i in range(self.conv_list.count())]
            with open(save_path, "wb") as f:
                f.write(img2pdf.convert(img_paths, rotation=img2pdf.Rotation.ifvalid))
            QMessageBox.information(self, "Berhasil", "Gambar dikonversi!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFToolbox()
    window.show()
    sys.exit(app.exec())