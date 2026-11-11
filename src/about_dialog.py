"""Dialog Tentang Aplikasi - referensi tampilan dari aplikasi Flutter Rutinitasku."""

import random

from PyQt6.QtCore import QRectF, Qt, QTimer, QUrl
from PyQt6.QtGui import (QBrush, QColor, QDesktopServices, QFont, QIcon,
                         QLinearGradient, QPainter, QPainterPath, QPixmap)
from PyQt6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QSizePolicy, QTabWidget,
                             QVBoxLayout, QWidget)

from app_info import (APP_NAME, DEVELOPER_BIO, DEVELOPER_EMAIL,
                      DEVELOPER_LINKEDIN, DEVELOPER_NAME, DEVELOPER_TITLE,
                      PROJECT_URL, app_icon_path, profile_image_path,
                      read_version)

PRIMARY = "#283593"
PRIMARY_LIGHT = "#3949ab"
ACCENT = "#00897b"

FEATURES = [
    ("📄", "Gabung PDF + Gambar",
     "Satukan beberapa file PDF, PNG, JPG, dan JPEG menjadi satu dokumen PDF "
     "dengan urutan yang bisa Anda atur sendiri."),
    ("🖼️", "Konversi Massal Gambar ke PDF",
     "Ubah banyak gambar sekaligus menjadi satu PDF tanpa perlu file PDF lain, "
     "praktis untuk arsip scan atau foto dokumen."),
    ("📐", "Ukuran Kertas Fleksibel",
     "Pilih A4, F4/Folio, Letter, Legal, atau ikuti ukuran asli gambar sesuai "
     "kebutuhan pencetakan Anda."),
    ("↕️", "Margin per Sisi",
     "Atur margin atas, bawah, kiri, dan kanan secara terpisah dalam satuan "
     "milimeter agar hasil cetak selalu rapi."),
    ("👁️", "Preview Live",
     "Lihat langsung bentuk halaman, area margin, dan thumbnail gambar pertama "
     "sebelum proses penggabungan dijalankan."),
    ("💾", "Preset Margin Tersimpan",
     "Simpan kombinasi margin favorit dan pakai ulang kapan saja. Pengaturan "
     "terakhir juga otomatis diingat antar sesi."),
    ("📥", "Drag & Drop + Urutkan",
     "Tarik file langsung dari folder ke daftar, lalu geser urutannya dengan "
     "tombol Atas/Bawah atau hapus file yang tidak dipakai."),
    ("🔒", "100% Offline & Privasi",
     "Semua proses berjalan lokal di komputer Anda. Tidak ada file yang "
     "diunggah ke internet, sehingga data tetap aman."),
]

VERSES = [
    ('"Serahkanlah perbuatanmu kepada TUHAN,\n'
     'maka terlaksanalah segala rencanamu."', "— Amsal 16:3 —"),
    ('"Bukan kepada kami, ya TUHAN, bukan kepada kami,\n'
     'tetapi kepada nama-Mulah beri kemuliaan,\n'
     'oleh karena kasih-Mu, oleh karena setia-Mu!"', "— Mazmur 115:1 —"),
    ('"Apapun juga yang kamu perbuat,\n'
     'perbuatlah dengan segenap hatimu\n'
     'seperti untuk Tuhan dan bukan untuk manusia."', "— Kolose 3:23 —"),
    ('"Percayalah kepada TUHAN dengan segenap hatimu,\n'
     'dan janganlah bersandar kepada pengertianmu sendiri.\n'
     'Akuilah Dia dalam segala lakumu,\n'
     'maka Ia akan meluruskan jalanmu."', "— Amsal 3:5-6 —"),
]

DEDICATION = (
    "Puji dan syukur yang tak terhingga kepada TUHAN atas hikmat, kekuatan, "
    "dan tuntunan-Nya yang sempurna dari awal perancangan hingga "
    "terselesaikannya aplikasi ini. Segala kemuliaan hanya bagi nama-Nya."
)


class AvatarWidget(QWidget):
    """Foto profil bulat dengan cincin gradien."""

    def __init__(self, image_path, size=136, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._pixmap = QPixmap(image_path)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(PRIMARY))
        gradient.setColorAt(1.0, QColor(ACCENT))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QRectF(0, 0, self.width(), self.height()))

        inner = QRectF(5, 5, self.width() - 10, self.height() - 10)
        path = QPainterPath()
        path.addEllipse(inner)
        painter.setClipPath(path)

        if self._pixmap.isNull():
            painter.fillRect(inner, QColor("#e0e0e0"))
            return

        scaled = self._pixmap.scaled(
            inner.size().toSize(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        offset_x = (scaled.width() - inner.width()) / 2
        offset_y = (scaled.height() - inner.height()) / 2
        painter.drawPixmap(
            QRectF(inner.x() - offset_x, inner.y() - offset_y,
                   scaled.width(), scaled.height()),
            scaled,
            QRectF(scaled.rect()),
        )


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tentang {APP_NAME}")
        self.setWindowIcon(QIcon(app_icon_path()))
        self.setMinimumSize(540, 580)
        self.resize(640, 720)

        self._verse_index = random.randrange(len(VERSES))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        tabs = QTabWidget()
        tabs.addTab(self._build_features_tab(), "Fitur Aplikasi")
        tabs.addTab(self._build_developer_tab(), "Pengembang")
        layout.addWidget(tabs)

        self._verse_timer = QTimer(self)
        self._verse_timer.timeout.connect(self._next_verse)
        self._verse_timer.start(30000)
        self._apply_verse()

    # ---------------------------------------------------------------- Fitur
    def _build_features_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        for icon, title, subtitle in FEATURES:
            layout.addWidget(self._feature_card(icon, title, subtitle))
        layout.addStretch(1)

        scroll.setWidget(container)
        return scroll

    def _feature_card(self, icon, title, subtitle):
        card = QFrame()
        card.setObjectName("FeatureCard")
        card.setStyleSheet(
            "QFrame#FeatureCard {"
            "  background: #ffffff;"
            "  border: 1px solid #e0e0e0;"
            "  border-radius: 12px;"
            "}"
        )

        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(14)

        icon_label = QLabel(icon)
        icon_label.setFixedWidth(44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSizeF(18)
        icon_label.setFont(font)
        row.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSizeF(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {PRIMARY}; border: none;")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("color: #546e7a; font-size: 12px; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        row.addLayout(text_layout, 1)
        return card

    # ------------------------------------------------------------ Pengembang
    def _build_developer_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 18, 28, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Kartu dedikasi + ayat
        verse_card = QFrame()
        verse_card.setObjectName("VerseCard")
        verse_card.setStyleSheet(
            "QFrame#VerseCard {"
            f"  background: rgba(40, 53, 147, 0.05);"
            f"  border: 1.5px solid rgba(40, 53, 147, 0.20);"
            "  border-radius: 16px;"
            "}"
            "QLabel { border: none; background: transparent; }"
        )
        verse_layout = QVBoxLayout(verse_card)
        verse_layout.setContentsMargins(20, 16, 20, 16)
        verse_layout.setSpacing(8)

        quote = QLabel("❝")
        quote_font = QFont()
        quote_font.setPointSizeF(22)
        quote.setFont(quote_font)
        quote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quote.setStyleSheet(f"color: {PRIMARY};")
        verse_layout.addWidget(quote)

        self.verse_label = QLabel("")
        self.verse_label.setWordWrap(True)
        self.verse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verse_label.setStyleSheet(
            "color: #37474f; font-style: italic; font-weight: 600; font-size: 13px;"
        )
        verse_layout.addWidget(self.verse_label)

        self.ref_label = QLabel("")
        self.ref_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_label.setStyleSheet(
            f"color: {PRIMARY}; font-weight: bold; font-size: 12px;"
        )
        verse_layout.addWidget(self.ref_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(40, 53, 147, 0.15);")
        divider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        verse_layout.addWidget(divider)

        dedication = QLabel(DEDICATION)
        dedication.setWordWrap(True)
        dedication.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dedication.setStyleSheet("color: #546e7a; font-size: 12px; line-height: 1.5;")
        verse_layout.addWidget(dedication)
        layout.addWidget(verse_card)

        layout.addSpacing(10)

        avatar_row = QHBoxLayout()
        avatar_row.addStretch(1)
        avatar_row.addWidget(AvatarWidget(profile_image_path()))
        avatar_row.addStretch(1)
        layout.addLayout(avatar_row)

        name = QLabel(DEVELOPER_NAME)
        name_font = QFont()
        name_font.setPointSizeF(15)
        name_font.setBold(True)
        name.setFont(name_font)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(f"color: {PRIMARY};")
        layout.addWidget(name)

        title = QLabel(DEVELOPER_TITLE)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #455a64; font-size: 13px;")
        layout.addWidget(title)

        bio = QLabel(DEVELOPER_BIO)
        bio.setWordWrap(True)
        bio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bio.setStyleSheet("color: #546e7a; font-size: 12px;")
        bio.setFixedWidth(480)
        bio.setMinimumHeight(96)
        bio.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        layout.addWidget(bio, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(6)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        buttons.addWidget(self._link_button("LinkedIn", DEVELOPER_LINKEDIN))
        buttons.addWidget(self._link_button("Email", f"mailto:{DEVELOPER_EMAIL}"))
        buttons.addWidget(self._link_button("GitHub", PROJECT_URL))
        buttons.addStretch(1)
        layout.addLayout(buttons)

        layout.addSpacing(8)
        version = QLabel(f"Versi {read_version()}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #90a4ae; font-size: 11px;")
        layout.addWidget(version)

        scroll.setWidget(container)
        return scroll

    def _link_button(self, text, url):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            "QPushButton {"
            f"  color: {PRIMARY};"
            "  background: transparent;"
            "  border: 1px solid rgba(40, 53, 147, 0.35);"
            "  border-radius: 16px;"
            "  padding: 6px 16px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(40, 53, 147, 0.08);"
            "}"
        )
        button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(url))
        )
        return button

    # ---------------------------------------------------------------- Ayat
    def _next_verse(self):
        self._verse_index = (self._verse_index + 1) % len(VERSES)
        self._apply_verse()

    def _apply_verse(self):
        text, ref = VERSES[self._verse_index]
        self.verse_label.setText(text)
        self.ref_label.setText(ref)
