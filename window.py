import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QSize
from view import View

def create_line_icon(width, size=QSize(32, 32)):
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(0, 0, 0))  # Black color
    pen.setWidth(width)
    painter.setPen(pen)
    painter.drawLine(4, size.height() // 2, size.width() - 4, size.height() // 2)
    painter.end()
    return QIcon(pixmap)

class Window(QtWidgets.QMainWindow):
    def __init__(self, position=(0, 0), dimension=(500, 300)):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle("CAI  2425A : New File ")
        x, y = position
        w, h = dimension

        self.view = View()       
        self.scene = QtWidgets.QGraphicsScene()   # model 
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        self.view.setGeometry(x, y, w, h)
        self.scene.setSceneRect(x, y, w, h)

        self.create_actions()
        self.connect_actions()
        self.create_menus()
        self.create_toolbar()

        self.filename = None
 
    def get_view(self):
        return self.view

    def set_view(self, view):
        self.view = view

    def get_scene(self):
        return self.scene

    def set_scene(self, scene):
        self.scene = scene

    def create_actions(self):
        # File actions
        self.action_file_new = QtWidgets.QAction(QtGui.QIcon('Icons/new.png'), "New", self)
        self.action_file_new.setShortcut("Ctrl+N")
        self.action_file_new.setStatusTip("Create a new file")

        self.action_file_open = QtWidgets.QAction(QtGui.QIcon('Icons/open.png'), "Open", self)
        self.action_file_open.setShortcut("Ctrl+O")
        self.action_file_open.setStatusTip("Open file")

        self.action_file_save = QtWidgets.QAction(QtGui.QIcon('Icons/save.png'), "Save", self)
        self.action_file_save.setShortcut("Ctrl+S")
        self.action_file_save.setStatusTip("Save file")

        self.action_file_save_as = QtWidgets.QAction(QtGui.QIcon('Icons/save_as.png'), "Save as", self)
        self.action_file_save_as.setStatusTip("Save as")

        # Tools actions
        self.action_tools = QtWidgets.QActionGroup(self)
        self.action_tools.setExclusive(True)

        self.action_tools_select = QtWidgets.QAction(QtGui.QIcon('Icons/select_cursor.png'), self.tr("&Select"), self)
        self.action_tools_select.setCheckable(True)
        self.action_tools_select.setChecked(True)
        self.action_tools.addAction(self.action_tools_select)

        self.action_tools_text = QtWidgets.QAction(QtGui.QIcon('Icons/tool_text.png'), self.tr("&Text"), self)
        self.action_tools_text.setCheckable(True)
        self.action_tools.addAction(self.action_tools_text)

        self.action_tools_pen = QtWidgets.QAction(QtGui.QIcon('Icons/tool_pen.png'), self.tr("&Pen"), self)
        self.action_tools_pen.setCheckable(True)
        self.action_tools.addAction(self.action_tools_pen)

        self.action_tools_line = QtWidgets.QAction(QtGui.QIcon('Icons/tool_line.png'), self.tr("&Line"), self)
        self.action_tools_line.setCheckable(True)
        self.action_tools.addAction(self.action_tools_line)

        self.action_tools_rectangle = QtWidgets.QAction(QtGui.QIcon('Icons/tool_rectangle.png'), self.tr("&Rectangle"), self)
        self.action_tools_rectangle.setCheckable(True)
        self.action_tools.addAction(self.action_tools_rectangle)

        self.action_tools_polygon = QtWidgets.QAction(QtGui.QIcon('Icons/tool_polygon.png'), self.tr("&Polygone"), self)
        self.action_tools_polygon.setCheckable(True)
        self.action_tools.addAction(self.action_tools_polygon)

        # Style actions    
        self.action_style_pen_color = QtWidgets.QAction(QtGui.QIcon('Icons/colorize.png'), self.tr("&Color"), self)
        self.action_style_text_color = QtWidgets.QAction(QtGui.QIcon('Icons/colorize.png'), self.tr("&Color"), self)

        self.action_edit_undo = QtWidgets.QAction(QtGui.QIcon('Icons/undo.png'), "Undo", self)
        self.action_edit_undo.setShortcut("Ctrl+Z")
        self.action_edit_undo.setStatusTip("Undo last action")

        self.action_edit_redo = QtWidgets.QAction(QtGui.QIcon('Icons/redo.png'), "Redo", self)
        self.action_edit_redo.setShortcut("Ctrl+Y")
        self.action_edit_redo.setStatusTip("Redo last undone action")

        # Pen size actions
        self.action_pen_size = QtWidgets.QActionGroup(self)
        self.action_pen_size.setExclusive(True)

        #Undo redo
        #self.action_tools_undo = QtWidgets.QActionGroup(self)
        #self.action_tools_redo = QtWidgets.QActionGroup(self)

        pen_sizes = [1, 3, 5, 8]
        for size in pen_sizes:
            action = QtWidgets.QAction(create_line_icon(size), f"{size}px", self)
            action.setCheckable(True)
            action.setData(size)
            self.action_pen_size.addAction(action)

        # Set 1px as default
        self.action_pen_size.actions()[0].setChecked(True)

    def connect_actions(self):
        self.action_file_new.triggered.connect(self.file_new)
        self.action_file_open.triggered.connect(self.file_open)
        self.action_file_save.triggered.connect(self.save)
        self.action_file_save_as.triggered.connect(self.save_as)

        # Connecting tool selection actions
        self.action_tools_select.triggered.connect(lambda checked, tool="select": self.tools_selection(checked, tool))
        self.action_tools_text.triggered.connect(lambda checked, tool="text": self.tools_selection(checked, tool))
        self.action_tools_pen.triggered.connect(lambda checked, tool="pen": self.tools_selection(checked, tool))
        self.action_tools_line.triggered.connect(lambda checked, tool="line": self.tools_selection(checked, tool))
        self.action_tools_rectangle.triggered.connect(lambda checked, tool="rectangle": self.tools_selection(checked, tool))
        self.action_tools_polygon.triggered.connect(lambda checked, tool="polygon": self.tools_selection(checked, tool))


        self.action_style_pen_color.triggered.connect(self.style_pen_color_selection)
        self.action_style_text_color.triggered.connect(self.style_text_color_selection)

        self.action_edit_undo.triggered.connect(self.view.undo)
        self.action_edit_redo.triggered.connect(self.view.redo)

        # Connect pen size actions
        for action in self.action_pen_size.actions():
            action.triggered.connect(self.set_pen_size)

    def create_toolbar(self):
        toolbar = self.addToolBar("Drawing Tools")        
        toolbar.addAction(self.action_tools_select)
        toolbar.addAction(self.action_tools_text)
        toolbar.addAction(self.action_tools_pen)
        
        # Style the toolbar
        toolbar.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
            }
            QToolButton:hover {
                background-color: #89CFF0;
            }
            QToolButton:checked {
                background-color: #007FFF;
            }
            """)

    def file_new(self):
        if self.maybe_save():
            self.scene.clear()
            self.filename = None
            self.view.resetTransform()
            self.setWindowTitle("CAI 2425A : - New File")

    def file_open(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", os.getcwd(), "Shape Files (*.json)")
        if filename:
            self.filename = filename
            self.load_shapes(filename)

    def save(self):
        if self.filename:
            return self.save_shapes(self.filename)
        else:
            return self.save_as()

    def save_as(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", os.getcwd(), "Shape Files (*.json)")
        if filename:
            self.filename = filename
            return self.save_shapes(filename)
        return False

    def save_shapes(self, filename):
        shapes = []
        for item in self.scene.items():
            if isinstance(item, QtWidgets.QGraphicsLineItem):
                shape_data = {
                    'type': 'line',
                    'start': (item.line().x1(), item.line().y1()),
                    'end': (item.line().x2(), item.line().y2()),
                    'color': item.pen().color().name(),
                    'width': item.pen().width()
                }
            elif isinstance(item, QtWidgets.QGraphicsRectItem):
                shape_data = {
                    'type': 'rect',
                    'rect': (item.rect().x(), item.rect().y(), item.rect().width(), item.rect().height()),
                    'color': item.pen().color().name(),
                    'width': item.pen().width(),
                    'brush-color': item.brush().color().name(),
                    'brush-style': item.brush().style()
                }
            elif isinstance(item, QtWidgets.QGraphicsPathItem):  # Handling freehand pen drawings
                shape_data = {
                    'type': 'path',
                    'path': [[(point.x(), point.y()) for point in polygon] for polygon in item.path().toSubpathPolygons()],
                    'color': item.pen().color().name(),
                    'width': item.pen().width()
                }
            elif isinstance(item, QtWidgets.QGraphicsTextItem):
                shape_data = {
                    'type': 'text',
                    'text': item.toPlainText(),
                    'pos': (item.pos().x(), item.pos().y()),
                    'font': item.font().toString(),
                    'color': item.defaultTextColor().name()
                }
            else:
                continue  # Skip unsupported item types
            shapes.append(shape_data)

        try:
            with open(filename, 'w') as file:
                json.dump(shapes, file)
            return True
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Save Error", f"Failed to save file: {str(e)}")
            return False

    def load_shapes(self, filename):
        with open(filename, 'r') as file:
            shapes = json.load(file)

        self.scene.clear()

        for shape in shapes:
            if shape['type'] == 'line':
                line_item = QtWidgets.QGraphicsLineItem(*shape['start'], *shape['end'])
                pen = QtGui.QPen(QtGui.QColor(shape['color']))
                pen.setWidth(shape['width'])
                line_item.setPen(pen)
                self.scene.addItem(line_item)
            elif shape['type'] == 'rect':
                rect_item = QtWidgets.QGraphicsRectItem(*shape['rect'])
                pen = QtGui.QPen(QtGui.QColor(shape['color']))
                pen.setWidth(shape['width'])
                bru = QtGui.QBrush(QtGui.QColor(shape['brush-color']))
                bru.setStyle(QtCore.Qt.BrushStyle(shape['brush-style']))
                rect_item.setPen(pen)
                rect_item.setBrush(bru)
                self.scene.addItem(rect_item)
            elif shape['type'] == 'path':  # Loading freehand pen drawings
                path = QtGui.QPainterPath()
                for polygon in shape['path']:
                    path.addPolygon(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in polygon]))
                path_item = QtWidgets.QGraphicsPathItem(path)
                pen = QtGui.QPen(QtGui.QColor(shape['color']))
                pen.setWidth(shape['width'])
                path_item.setPen(pen)
                self.scene.addItem(path_item)
            elif shape['type'] == 'text':
                text_item = QtWidgets.QGraphicsTextItem(shape['text'])
                text_item.setPos(QtCore.QPointF(*shape['pos']))
                font = QtGui.QFont()
                font.fromString(shape['font'])
                text_item.setFont(font)
                text_item.setDefaultTextColor(QtGui.QColor(shape['color']))
                self.scene.addItem(text_item)

    def maybe_save(self):
        if self.scene.items():
            reply = QtWidgets.QMessageBox.question(
                self, "Save Changes",
                "Do you want to save your changes?",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            if reply == QtWidgets.QMessageBox.Save:
                return self.save()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return False
        return True

    def tools_selection(self, checked, tool):
        print("Window.tools_selection()")
        print("checked : ", checked)
        print("tool : ", tool)
        self.view.set_tool(tool)

    def style_pen_color_selection(self):
        color = QtWidgets.QColorDialog.getColor(QtCore.Qt.yellow, self)
        if color.isValid():
            self.view.set_pen_color(color.name())

    def style_text_color_selection(self):
        color = QtWidgets.QColorDialog.getColor(QtCore.Qt.black, self)
        if color.isValid():
            self.view.set_text_color(color.name())

    def set_pen_size(self):
        action = self.sender()
        if isinstance(action, QtWidgets.QAction):
            size = action.data()
            pen = self.view.get_pen()
            pen.setWidth(size)
            self.view.set_pen(pen)
            print(f"Pen size set to: {size}")


    def create_menus(self):
        # Menubar actions
        menubar = self.menuBar()
        menu_file = menubar.addMenu('&File')
        menu_file.addAction(self.action_file_new)
        menu_file.addAction(self.action_file_open)
        menu_file.addAction(self.action_file_save)
        menu_file.addAction(self.action_file_save_as)

        menu_tool = menubar.addMenu('&Tools')
        menu_tool.addAction(self.action_tools_select)
        menu_tool.addAction(self.action_tools_text)
        menu_tool.addAction(self.action_tools_pen)
        menu_tool.addAction(self.action_tools_line)
        menu_tool.addAction(self.action_tools_rectangle)
        menu_tool.addAction(self.action_tools_polygon)

        menu_style = menubar.addMenu('&Style')
        menu_style_pen = menu_style.addMenu(QtGui.QIcon('Icons/tool_pen.png'),'&Pen')
        menu_style_pen.addAction(self.action_style_pen_color)
        menu_style_text = menu_style.addMenu(QtGui.QIcon('Icons/tool_text.png'),'&Text')
        menu_style_text.addAction(self.action_style_text_color)

        #menu_undo = menubar.addMenu('&Undo')
        #menu_undo.setIcon(QtGui.QIcon('Icons/undo.png'))
        #menu_undo.addAction(self.action_tools_undo)
        #menu_redo = menubar.addMenu('Redo')
        #menu_redo.setIcon(QtGui.QIcon('Icons/redo.png'))
        #menu_redo.addAction(self.action_tools_redo)

        menubar.addAction(self.action_edit_undo)
        menubar.addAction(self.action_edit_redo)
        
        # Create Size submenu
        menu_style_pen_size = menu_style_pen.addMenu(QtGui.QIcon('Icons/width.png'),'&Size')
        for action in self.action_pen_size.actions():
            menu_style_pen_size.addAction(action)

        stylesheet = """
        QMenu::item:selected {
            background-color: #89CFF0;
            color: black;
        }
        QMenu::item:checked {
            background-color: #007FFF;
        }
        """
        for menu in [menu_file, menu_tool, menu_style, menu_style_pen, menu_style_pen_size]:
            menu.setStyleSheet(stylesheet)

        # Statusbar 
        statusbar = self.statusBar()

    def resizeEvent(self, event):
        print("MainWindow.resizeEvent() : View")
        if self.view:
            print("dx : ", self.size().width() - self.view.size().width())
            print("dy : ", self.size().height() - self.view.size().height())
        else:
            print("MainWindow needs a view!")
        print("menubar size : ", self.menuBar().size())

    def contextMenuEvent(self, event):
            contextMenu = QtWidgets.QMenu(self)
            toolAct = contextMenu.addAction("Tools")
            deleteAct = contextMenu.addAction("Delete")
            quitAct = contextMenu.addAction("Quit")
            action = contextMenu.exec_(self.mapToGlobal(event.pos()))
            if action == quitAct:
                self.close()

if __name__ == "__main__":
    print(QtCore.QT_VERSION_STR)
    app = QtWidgets.QApplication(sys.argv)

    position = 0, 0
    dimension = 600, 400

    mw = Window(position, dimension)

    offset = 5
    xd, yd = offset, offset
    xf, yf = 200 + offset, 100 + offset
    line = QtWidgets.QGraphicsLineItem(xd, yd, xf, yf)
    line.setPen(mw.get_view().get_pen())
    mw.get_scene().addItem(line)

    mw.show()

    sys.exit(app.exec_())