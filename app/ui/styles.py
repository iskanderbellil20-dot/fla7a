APP_STYLE = """
QMainWindow {
    background-color: #f4f6f8;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 14px;
    color: #1f2937;
}

#sidebar {
    background-color: #163b32;
}

#appTitle {
    color: white;
    font-size: 21px;
    font-weight: 700;
}

#appSubtitle {
    color: #b9d4ca;
    font-size: 12px;
}

QPushButton#navigationButton {
    background-color: transparent;
    color: #e9f2ef;
    border: none;
    border-radius: 7px;
    text-align: left;
    padding: 12px 16px;
    font-size: 14px;
}

QPushButton#navigationButton:hover {
    background-color: #245649;
}

QPushButton#navigationButton:checked {
    background-color: #2f6f5e;
    color: white;
    font-weight: 600;
}

#contentArea {
    background-color: #f4f6f8;
}

#pageTitle {
    font-size: 28px;
    font-weight: 700;
    color: #17252a;
}

#pageDescription {
    font-size: 14px;
    color: #667085;
}
QLineEdit,
QComboBox,
QTextEdit {
    background-color: white;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    padding: 8px;
}

QLineEdit:focus,
QComboBox:focus,
QTextEdit:focus {
    border: 1px solid #2f6f5e;
}

QPushButton {
    padding: 8px 14px;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    background-color: white;
}

QPushButton:hover {
    background-color: #f0f3f2;
}

QPushButton#primaryButton {
    background-color: #2f6f5e;
    color: white;
    border: none;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #245649;
}

QTableWidget {
    background-color: white;
    border: 1px solid #e0e4e7;
    border-radius: 6px;
    gridline-color: #edf0f2;
    alternate-background-color: #f8faf9;
}

QHeaderView::section {
    background-color: #edf2f0;
    padding: 9px;
    border: none;
    border-bottom: 1px solid #d8dfdc;
    font-weight: 600;
}
"""