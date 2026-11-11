import sys
import os
import io
import json
import img2pdf
from PIL import Image, ImageOps
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QListWidget, QFileDialog, QMessageBox, QHBoxLayout,
                             QTabWidget, QLabel, QComboBox, QGroupBox, QGridLayout,
                             QDoubleSpinBox, QInputDialog, QSplitter, QSizePolicy)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QFont

# Definisi ukuran kertas dalam satuan milimeter (Lebar, Tinggi)
# None berarti halaman mengikuti ukuran asli gambar.
PAPER_SIZES_MM = {
    "Ukuran Asli Gambar (Default)": None,
    "A4 (210 x 297 mm)": (210, 297),
    "F4 / Folio (215 x 330 mm)": (215, 330),
    "Letter (8.5 x 11 inci)": (215.9, 279.4),
    "Legal (8.5 x 14 inci)": (215.9, 355.6),
}

# Preset margin bawaan (atas, bawah, kiri, kanan) dalam mm
BUILTIN_MARGIN_PRESETS = {
    "Tanpa Margin (0 mm)": (0.0, 0.0, 0.0, 0.0),
    "Normal (20 mm)": (20.0, 20.0, 20.0, 20.0),
    "Sempit (10 mm)": (10.0, 10.0, 10.0, 10.0),
}

CUSTOM_PRESET = "Custom..."
SETTINGS_ORG = "PDFToolbox"
SETTINGS_APP = "PDFToolbox"


def build_image_page(image_path, paper_pt, margin_pt):
    """Buat satu halaman PDF seukuran kertas dengan gambar di area konten.

    img2pdf selalu menempatkan gambar di tengah halaman, jadi gambar dibuat
    pada halaman seukuran area konten (kertas dikurangi margin), lalu ditempel
    ke halaman kosong pada posisi (kiri, bawah) sesuai margin.
    """
    top, bottom, left, right = margin_pt
    content_w = paper_pt[0] - left - right
    content_h = paper_pt[1] - top - bottom
    if content_w <= 0 or content_h <= 0:
        raise ValueError("Area konten terlalu kecil. Periksa kembali nilai margin.")

    pdf_bytes = img2pdf.convert(
        image_path,
        rotation=img2pdf.Rotation.ifvalid,
        layout_fun=img2pdf.get_layout_fun(pagesize=(content_w, content_h)),
    )
    inner_page = PdfReader(io.BytesIO(pdf_bytes)).pages[0]

    page = PageObject.create_blank_page(width=paper_pt[0], height=paper_pt[1])
    inner_page.add_transformation(Transformation().translate(tx=left, ty=bottom))
    page.merge_page(inner_page)
    return page


def validate_margins(paper_pt, margin_pt):
    """Kembalikan pesan error bila margin tidak masuk akal, atau None."""
    if paper_pt is None:
        return None
    top, bottom, left, right = margin_pt
    if left + right >= paper_pt[0] or top + bottom >= paper_pt[1]:
        return ("Total margin kiri + kanan atau atas + bawah terlalu besar "
                "untuk ukuran kertas yang dipilih.")

    # Sisakan minimal ~7 mm agar gambar masih terlihat
    min_content = img2pdf.mm_to_pt(7)
    if (paper_pt[0] - left - right) < min_content or \
            (paper_pt[1] - top - bottom) < min_content:
        return "Area konten terlalu kecil. Kurangi nilai margin."
    return None


def load_thumbnail(path, max_side=1000):
    """Muat gambar sebagai QPixmap, dengan koreksi orientasi EXIF."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue(), "PNG")
    return pixmap


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
                if file_path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    self.addItem(file_path)
        else:
            event.ignore()


class PagePreview(QWidget):
    """Panel preview live: kertas, area margin, dan thumbnail gambar pertama."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.paper_pt = None
        self.margin_pt = (0.0, 0.0, 0.0, 0.0)
        self.image_path = None
        self.note = ""
        self._pixmap = None
        self._pixmap_path = None

    def set_preview(self, paper_pt, margin_pt, image_path, note=""):
        self.paper_pt = paper_pt
        self.margin_pt = margin_pt or (0.0, 0.0, 0.0, 0.0)
        self.note = note
        if image_path != self._pixmap_path:
            self._pixmap_path = image_path
            self._pixmap = None
            if image_path and os.path.exists(image_path):
                try:
                    self._pixmap = load_thumbnail(image_path)
                except Exception:
                    self._pixmap = None
        self.update()

    def _draw_image_fit(self, painter, rect):
        if self._pixmap is None or self._pixmap.isNull():
            return
        if rect.width() <= 0 or rect.height() <= 0:
            return
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        scale = min(rect.width() / pw, rect.height() / ph)
        iw, ih = pw * scale, ph * scale
        target = QRectF(rect.x() + (rect.width() - iw) / 2,
                        rect.y() + (rect.height() - ih) / 2, iw, ih)
        painter.save()
        painter.setClipRect(rect)
        painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#eceff1"))

        avail = self.rect().adjusted(18, 18, -18, -34)
        note = self.note

        # Tentukan ukuran halaman yang digambar
        if self.paper_pt is not None:
            page_w, page_h = self.paper_pt
        elif self._pixmap is not None and not self._pixmap.isNull():
            page_w, page_h = self._pixmap.width(), self._pixmap.height()
        else:
            page_w, page_h = 210.0, 297.0

        if page_w <= 0 or page_h <= 0 or avail.width() <= 0 or avail.height() <= 0:
            return

        scale = min(avail.width() / page_w, avail.height() / page_h)
        w, h = page_w * scale, page_h * scale
        x = avail.x() + (avail.width() - w) / 2
        y = avail.y() + (avail.height() - h) / 2
        page_rect = QRectF(x, y, w, h)

        # Bayangan + kertas
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 45))
        painter.drawRoundedRect(page_rect.translated(4, 4), 3, 3)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#b0bec5"), 1))
        painter.drawRect(page_rect)

        if self.paper_pt is not None:
            top, bottom, left, right = self.margin_pt
            content = QRectF(
                x + left * scale,
                y + top * scale,
                max(0.0, w - (left + right) * scale),
                max(0.0, h - (top + bottom) * scale),
            )
            if content.width() > 0 and content.height() > 0:
                self._draw_image_fit(painter, content)
                painter.setPen(QPen(QColor("#1976d2"), 1.2, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(content)

                # Label nilai margin (hanya jika ruang cukup)
                font = QFont()
                font.setPointSizeF(6.5)
                painter.setFont(font)
                painter.setPen(QColor("#1976d2"))
                align = Qt.AlignmentFlag.AlignCenter

                def label(value, rect):
                    if rect.width() >= 30 and rect.height() >= 12:
                        value_mm = value / img2pdf.mm_to_pt(1)
                        painter.drawText(rect, align, f"{value_mm:.1f} mm")

                def side_label(value, rect):
                    if rect.width() >= 14 and rect.height() >= 36:
                        value_mm = value / img2pdf.mm_to_pt(1)
                        painter.save()
                        painter.translate(rect.center())
                        painter.rotate(-90)
                        rotated = QRectF(-rect.height() / 2, -rect.width() / 2,
                                         rect.height(), rect.width())
                        painter.drawText(rotated, align, f"{value_mm:.1f} mm")
                        painter.restore()

                if top * scale >= 14:
                    label(top, QRectF(content.left(), y, content.width(), top * scale))
                if bottom * scale >= 14:
                    label(bottom, QRectF(content.left(), content.bottom(),
                                         content.width(), bottom * scale))
                side_label(left, QRectF(x, content.top(), left * scale, content.height()))
                side_label(right, QRectF(content.right(), content.top(),
                                         right * scale, content.height()))
        else:
            self._draw_image_fit(painter, page_rect)

        # Catatan di bawah preview
        if note:
            font = QFont()
            font.setPointSizeF(8)
            painter.setFont(font)
            painter.setPen(QColor("#b71c1c") if note.startswith("⚠") else QColor("#546e7a"))
            note_rect = QRectF(10, self.height() - 30, self.width() - 20, 26)
            painter.drawText(note_rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignHCenter, note)


class PaperSettings(QGroupBox):
    """Pengaturan ukuran kertas + preset/custom margin, tersimpan via QSettings."""

    changed = pyqtSignal()

    def __init__(self, key, parent=None):
        super().__init__("Ukuran Kertas dan Margin", parent)
        self.key = key
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._loading = False
        self.saved_presets = self._load_saved_presets()
        self._build_ui()
        self._load_state()

    # ---- Pembuatan UI ----
    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Ukuran kertas:"))
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(PAPER_SIZES_MM.keys())
        layout.addWidget(self.paper_combo)

        layout.addWidget(QLabel("Preset margin:"))
        self.preset_combo = QComboBox()
        layout.addWidget(self.preset_combo)

        grid = QGridLayout()
        grid.setContentsMargins(0, 4, 0, 0)
        self.spins = {}
        specs = [
            ("top", "Atas", 0, 0),
            ("bottom", "Bawah", 0, 2),
            ("left", "Kiri", 1, 0),
            ("right", "Kanan", 1, 2),
        ]
        for name, text, row, col in specs:
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 500.0)
            spin.setDecimals(1)
            spin.setSingleStep(1.0)
            spin.setSuffix(" mm")
            grid.addWidget(QLabel(text), row, col)
            grid.addWidget(spin, row, col + 1)
            self.spins[name] = spin
        layout.addLayout(grid)

        btn_layout = QHBoxLayout()
        self.btn_save_preset = QPushButton("💾 Simpan preset...")
        self.btn_delete_preset = QPushButton("🗑️ Hapus")
        btn_layout.addWidget(self.btn_save_preset)
        btn_layout.addWidget(self.btn_delete_preset)
        layout.addLayout(btn_layout)

        hint = QLabel("Margin hanya berlaku untuk file gambar. Halaman PDF disalin apa adanya.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #607d8b; font-size: 11px;")
        layout.addWidget(hint)
        layout.addStretch(1)

        self.paper_combo.currentIndexChanged.connect(self._on_paper_changed)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        for spin in self.spins.values():
            spin.valueChanged.connect(self._on_spin_changed)
        self.btn_save_preset.clicked.connect(self._save_preset)
        self.btn_delete_preset.clicked.connect(self._delete_preset)

    def _refresh_preset_combo(self):
        current = self.preset_combo.currentText()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItems(list(BUILTIN_MARGIN_PRESETS.keys()) +
                                   list(self.saved_presets.keys()) +
                                   [CUSTOM_PRESET])
        index = self.preset_combo.findText(current)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)

    # ---- QSettings ----
    def _load_saved_presets(self):
        raw = self.settings.value("margins/presets", "{}")
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        presets = {}
        for name, values in data.items():
            if isinstance(values, (list, tuple)) and len(values) == 4:
                try:
                    presets[name] = tuple(float(v) for v in values)
                except (TypeError, ValueError):
                    continue
        return presets

    def _save_saved_presets(self):
        self.settings.setValue("margins/presets", json.dumps(self.saved_presets))
        self.settings.sync()

    def _custom_values(self):
        raw = self.settings.value("margins/custom", "")
        try:
            data = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            data = {}
        values = []
        for name in ("top", "bottom", "left", "right"):
            try:
                values.append(float(data.get(name, 20.0)))
            except (TypeError, ValueError):
                values.append(20.0)
        return values

    def _store_custom_values(self):
        data = {name: spin.value() for name, spin in self.spins.items()}
        self.settings.setValue("margins/custom", json.dumps(data))

    def _save_current_custom(self):
        self._store_custom_values()
        self.settings.setValue(f"paper/{self.key}", self.paper_combo.currentText())
        self.settings.setValue(f"preset/{self.key}", self.preset_combo.currentText())

    def _load_state(self):
        self._loading = True
        self._refresh_preset_combo()

        paper = self.settings.value(f"paper/{self.key}", "A4 (210 x 297 mm)")
        index = self.paper_combo.findText(paper)
        if index >= 0:
            self.paper_combo.setCurrentIndex(index)

        top, bottom, left, right = self._custom_values()
        self.spins["top"].setValue(top)
        self.spins["bottom"].setValue(bottom)
        self.spins["left"].setValue(left)
        self.spins["right"].setValue(right)

        preset = self.settings.value(f"preset/{self.key}", "Normal (20 mm)")
        index = self.preset_combo.findText(preset)
        if index < 0:
            index = self.preset_combo.findText("Normal (20 mm)")
        self.preset_combo.setCurrentIndex(index)

        self._loading = False
        self._apply_preset_values()
        self._update_enabled()

    # ---- Event handler ----
    def _apply_preset_values(self):
        name = self.preset_combo.currentText()
        if name == CUSTOM_PRESET:
            return
        values = BUILTIN_MARGIN_PRESETS.get(name, self.saved_presets.get(name))
        if values is None:
            return
        self._loading = True
        for spin, value in zip(
                (self.spins["top"], self.spins["bottom"],
                 self.spins["left"], self.spins["right"]), values):
            spin.setValue(value)
        self._loading = False
        self._store_custom_values()

    def _update_enabled(self):
        has_paper = PAPER_SIZES_MM.get(self.paper_combo.currentText()) is not None
        is_custom = self.preset_combo.currentText() == CUSTOM_PRESET
        self.preset_combo.setEnabled(has_paper)
        for spin in self.spins.values():
            spin.setEnabled(has_paper and is_custom)
        self.btn_save_preset.setEnabled(has_paper and is_custom)
        self.btn_delete_preset.setEnabled(
            has_paper and self.preset_combo.currentText() in self.saved_presets)

    def _on_paper_changed(self):
        if self._loading:
            return
        self._update_enabled()
        self._save_current_custom()
        self.changed.emit()

    def _on_preset_changed(self):
        if self._loading:
            return
        self._apply_preset_values()
        self._update_enabled()
        self._save_current_custom()
        self.changed.emit()

    def _on_spin_changed(self):
        if self._loading:
            return
        self._store_custom_values()
        self._save_current_custom()
        self.changed.emit()

    # ---- Preset custom ----
    def _save_preset(self):
        name, ok = QInputDialog.getText(self, "Simpan Preset Margin",
                                        "Nama preset:")
        name = name.strip()
        if not ok or not name:
            return
        if name in BUILTIN_MARGIN_PRESETS or name == CUSTOM_PRESET:
            QMessageBox.warning(self, "Nama Tidak Valid",
                                "Nama tersebut sudah dipakai preset bawaan.")
            return
        if name in self.saved_presets:
            answer = QMessageBox.question(
                self, "Timpa Preset",
                f"Preset '{name}' sudah ada. Timpa dengan nilai sekarang?")
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.saved_presets[name] = tuple(spin.value() for spin in (
            self.spins["top"], self.spins["bottom"],
            self.spins["left"], self.spins["right"]))
        self._save_saved_presets()

        self.preset_combo.blockSignals(True)
        self._refresh_preset_combo()
        self.preset_combo.setCurrentText(name)
        self.preset_combo.blockSignals(False)
        self._update_enabled()
        self._save_current_custom()
        self.changed.emit()
        QMessageBox.information(self, "Tersimpan", f"Preset '{name}' disimpan.")

    def _delete_preset(self):
        name = self.preset_combo.currentText()
        if name not in self.saved_presets:
            return
        answer = QMessageBox.question(
            self, "Hapus Preset", f"Hapus preset '{name}'?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        del self.saved_presets[name]
        self._save_saved_presets()

        self.preset_combo.blockSignals(True)
        self._refresh_preset_combo()
        self.preset_combo.setCurrentText(CUSTOM_PRESET)
        self.preset_combo.blockSignals(False)
        self._update_enabled()
        self._save_current_custom()
        self.changed.emit()

    # ---- Nilai terpilih ----
    def paper_pt(self):
        size_mm = PAPER_SIZES_MM.get(self.paper_combo.currentText())
        if size_mm is None:
            return None
        return (img2pdf.mm_to_pt(size_mm[0]), img2pdf.mm_to_pt(size_mm[1]))

    def margins_mm(self):
        return tuple(self.spins[name].value()
                     for name in ("top", "bottom", "left", "right"))

    def margins_pt(self):
        if self.paper_pt() is None:
            return (0.0, 0.0, 0.0, 0.0)
        return tuple(img2pdf.mm_to_pt(v) for v in self.margins_mm())


class PDFToolbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Python PDF Toolbox - Custom Paper Size & Margin Edition')
        self.setGeometry(100, 100, 1100, 720)

        self.main_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_merger_tab(), "Merge PDF + Images")
        self.tabs.addTab(self.create_converter_tab(), "Bulk Image to PDF")

        self.main_layout.addWidget(self.tabs)
        self.setLayout(self.main_layout)
        self.tabs.currentChanged.connect(lambda _: self.update_preview(self._tab_key()))
        self.update_preview("merge")
        self.update_preview("converter")

    def _build_list_panel(self, list_widget, add_filter, extra_buttons, nav=True):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Tarik & Lepas (Drag & Drop) file dari folder ke sini:"))
        layout.addWidget(list_widget, 1)

        if nav:
            nav_layout = QHBoxLayout()
            btn_up = QPushButton('▲ Atas')
            btn_down = QPushButton('▼ Bawah')
            btn_up.clicked.connect(lambda: self.move_item(list_widget, -1))
            btn_down.clicked.connect(lambda: self.move_item(list_widget, 1))
            nav_layout.addWidget(btn_up)
            nav_layout.addWidget(btn_down)
            layout.addLayout(nav_layout)

        ctrl_layout = QHBoxLayout()
        btn_add = QPushButton('➕ Tambah Manual')
        btn_add.clicked.connect(lambda: self.add_files(list_widget, add_filter))
        ctrl_layout.addWidget(btn_add)
        for text, handler in extra_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            ctrl_layout.addWidget(btn)
        layout.addLayout(ctrl_layout)
        return panel

    def _build_tab(self, key, list_widget, add_filter, extra_buttons, nav,
                   run_text, run_color, run_handler):
        widget = QWidget()
        outer = QVBoxLayout(widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_list_panel(list_widget, add_filter,
                                                  extra_buttons, nav=nav))

        side = QWidget()
        side.setMinimumWidth(270)
        side.setMaximumWidth(460)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        settings = PaperSettings(key)
        preview = PagePreview()
        side_layout.addWidget(settings)
        side_layout.addWidget(preview, 1)
        splitter.addWidget(side)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([760, 320])
        outer.addWidget(splitter, 1)

        btn_run = QPushButton(run_text)
        btn_run.setStyleSheet(
            f"background-color: {run_color}; color: white; font-weight: bold; padding: 15px;")
        btn_run.clicked.connect(run_handler)
        outer.addWidget(btn_run)

        return widget, settings, preview

    def create_merger_tab(self):
        self.merge_list = DragDropListWidget()
        widget, self.merge_settings, self.merge_preview = self._build_tab(
            "merge",
            self.merge_list,
            "Semua (*.pdf *.png *.jpg *.jpeg)",
            [('❌ Hapus Terpilih', lambda: self.remove_selected(self.merge_list))],
            nav=True,
            run_text='PROSES PENGGABUNGAN',
            run_color='#2E7D32',
            run_handler=self.process_merge,
        )
        self._connect_preview(self.merge_list, self.merge_settings, "merge")
        return widget

    def create_converter_tab(self):
        self.conv_list = DragDropListWidget()
        widget, self.conv_settings, self.conv_preview = self._build_tab(
            "converter",
            self.conv_list,
            "Images (*.png *.jpg *.jpeg)",
            [('🗑️ Kosongkan', self.conv_list.clear)],
            nav=False,
            run_text='KONVERSI MASSAL KE PDF',
            run_color='#1565C0',
            run_handler=self.process_conversion,
        )
        self._connect_preview(self.conv_list, self.conv_settings, "converter")
        return widget

    def _connect_preview(self, list_widget, settings, key):
        settings.changed.connect(lambda: self.update_preview(key))
        model = list_widget.model()
        model.rowsInserted.connect(lambda *_: self.update_preview(key))
        model.rowsRemoved.connect(lambda *_: self.update_preview(key))
        model.layoutChanged.connect(lambda *_: self.update_preview(key))

    def _tab_key(self):
        return "merge" if self.tabs.currentIndex() == 0 else "converter"

    def update_preview(self, key):
        if key == "merge":
            settings, list_widget, preview = (
                self.merge_settings, self.merge_list, self.merge_preview)
        else:
            settings, list_widget, preview = (
                self.conv_settings, self.conv_list, self.conv_preview)

        paper = settings.paper_pt()
        margins = settings.margins_pt()
        image_path = None
        note = ""

        if list_widget.count() == 0:
            note = "Belum ada file. Tambahkan gambar untuk melihat preview."
        else:
            first = list_widget.item(0).text()
            if first.lower().endswith(".pdf"):
                note = "File pertama adalah PDF - halaman disalin tanpa perubahan margin."
            else:
                image_path = first

        error = validate_margins(paper, margins)
        if error:
            note = "⚠ " + error
        elif paper is None and image_path:
            note = "Ukuran asli gambar: margin tidak digunakan."

        preview.set_preview(paper, margins, image_path, note)

    # --- UTILITIES ---
    def add_files(self, list_widget, file_filter):
        files, _ = QFileDialog.getOpenFileNames(self, "Pilih File", "", file_filter)
        for f in files:
            list_widget.addItem(f)

    def remove_selected(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def move_item(self, list_widget, direction):
        curr_row = list_widget.currentRow()
        if curr_row == -1:
            return
        new_row = curr_row + direction
        if 0 <= new_row < list_widget.count():
            item = list_widget.takeItem(curr_row)
            list_widget.insertItem(new_row, item)
            list_widget.setCurrentRow(new_row)

    def _prepare_output(self, settings):
        paper = settings.paper_pt()
        margins = settings.margins_pt()
        error = validate_margins(paper, margins)
        if error:
            QMessageBox.warning(self, "Margin Tidak Valid", error)
            return None
        return paper, margins

    def _add_image(self, writer, readers, path, paper, margins):
        if paper is None:
            pdf_bytes = img2pdf.convert(path, rotation=img2pdf.Rotation.ifvalid)
            reader = PdfReader(io.BytesIO(pdf_bytes))
            readers.append(reader)
            writer.add_page(reader.pages[0])
        else:
            writer.add_page(build_image_page(path, paper, margins))

    def process_merge(self):
        if self.merge_list.count() == 0:
            return
        prepared = self._prepare_output(self.merge_settings)
        if prepared is None:
            return
        paper, margins = prepared
        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil", "", "PDF Files (*.pdf)")
        if not save_path:
            return

        writer = PdfWriter()
        readers = []
        try:
            for i in range(self.merge_list.count()):
                path = self.merge_list.item(i).text()
                if path.lower().endswith('.pdf'):
                    reader = PdfReader(path)
                    readers.append(reader)
                    for page in reader.pages:
                        writer.add_page(page)
                else:
                    self._add_image(writer, readers, path, paper, margins)

            with open(save_path, "wb") as f:
                writer.write(f)
            QMessageBox.information(self, "Berhasil", "File digabungkan!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def process_conversion(self):
        if self.conv_list.count() == 0:
            return
        prepared = self._prepare_output(self.conv_settings)
        if prepared is None:
            return
        paper, margins = prepared
        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return

        try:
            writer = PdfWriter()
            readers = []
            for i in range(self.conv_list.count()):
                path = self.conv_list.item(i).text()
                self._add_image(writer, readers, path, paper, margins)

            with open(save_path, "wb") as f:
                writer.write(f)
            QMessageBox.information(self, "Berhasil", "Gambar dikonversi!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFToolbox()
    window.show()
    sys.exit(app.exec())
