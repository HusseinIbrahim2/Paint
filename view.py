import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class TextToolbar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QHBoxLayout()
        
        self.font_family = QtWidgets.QFontComboBox()
        self.font_size = QtWidgets.QComboBox()
        font_sizes = ['8', '9', '10', '11', '12', '14', '16', '18', '20', '22', '24', '26', '28', '36', '48', '72']
        self.font_size.addItems(font_sizes)
        self.font_size.setEditable(True)
        
        self.bold_button = QtWidgets.QPushButton('B')
        self.bold_button.setCheckable(True)
        self.italic_button = QtWidgets.QPushButton('I')
        self.italic_button.setCheckable(True)
        self.underline_button = QtWidgets.QPushButton('U')
        self.underline_button.setCheckable(True)

        layout.addWidget(self.font_family)
        layout.addWidget(self.font_size)
        layout.addWidget(self.bold_button)
        layout.addWidget(self.italic_button)
        layout.addWidget(self.underline_button)

        self.setLayout(layout)

class Command:
    def execute(self):
        pass
    
    def undo(self):
        pass

class AddItemCommand(Command):
    def __init__(self, scene, item):
        self.scene = scene
        self.item = item
    
    def execute(self):
        self.scene.addItem(self.item)
    
    def undo(self):
        self.scene.removeItem(self.item)

class RemoveItemCommand(Command):
    def __init__(self, scene, item):
        self.scene = scene
        self.item = item
    
    def execute(self):
        self.scene.removeItem(self.item)
    
    def undo(self):
        self.scene.addItem(self.item)

class MoveItemCommand(Command):
    def __init__(self, item, old_pos, new_pos):
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self):
        self.item.setPos(self.new_pos)
    
    def undo(self):
        self.item.setPos(self.old_pos)

class View(QtWidgets.QGraphicsView):
    def __init__(self, position=(0,0), dimension=(600,400)):
        QtWidgets.QGraphicsView.__init__(self)
        x, y = position
        w, h = dimension
        self.setGeometry(x, y, w, h)

        self.begin, self.end = QtCore.QPoint(0,0), QtCore.QPoint(0,0)
        self.pen, self.brush = None, None
        self.tool = "select"
        self.selected_items = []
        self.rubberBand = None
        self.dragging = False
        self.drag_start_pos = None
        self.item_original_positions = {}
        self.current_path = None
        self.current_text_item = None
        self.undo_stack = []
        self.redo_stack = []
        
        self.create_style()
        self.temp_item = None  # Temporary item for real-time drawing
        
        self.text_toolbar = TextToolbar(self)
        self.text_toolbar.hide()
        
        self.current_font = QtGui.QFont()
        self.text_color = QtGui.QColor(QtCore.Qt.black)
        self.original_colors = {}

        self.polygons = []
        self.current_polygon = []
        self.drawing_polygon = False
        
        # Connect toolbar signals
        self.text_toolbar.font_family.currentFontChanged.connect(self.update_font)
        self.text_toolbar.font_size.currentTextChanged.connect(self.update_font)
        self.text_toolbar.bold_button.toggled.connect(self.update_font)
        self.text_toolbar.italic_button.toggled.connect(self.update_font)
        self.text_toolbar.underline_button.toggled.connect(self.update_font)

    def __repr__(self):
        return "<View({},{},{})>".format(self.pen, self.brush, self.tool)
    
    def get_pen(self):
        return self.pen
    
    def set_text_color(self, color):
        self.text_color = QtGui.QColor(color)
        if self.current_text_item:
            self.current_text_item.setDefaultTextColor(self.text_color)
        # Update the color of selected text items
        for item in self.selected_items:
            if isinstance(item, QtWidgets.QGraphicsTextItem):
                item.setDefaultTextColor(self.text_color)

    def set_pen(self, pen):
        self.pen = QtGui.QPen(pen)

    def set_pen_color(self, color):
        print("View.set_pen_color(self,color)", color)
        self.pen.setColor(QtGui.QColor(color))

    def get_brush(self):
        return self.brush

    def set_brush(self, brush):
        self.brush = brush

    def set_brush_color(self, color):
        print("View.set_brush_color(self,color)", color)
        self.brush.setColor(QtGui.QColor(color))

    def get_tool(self):
        return self.tool

    def set_tool(self, tool):
        print("View.set_tool(self,tool)", tool)
        if self.tool == "text":
            self.finalize_text_input()
        self.tool = tool
        if tool == "text":
            self.setCursor(QtCore.Qt.IBeamCursor)
            self.show_text_toolbar()
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.hide_text_toolbar()

    def create_style(self):
        self.create_pen()
        self.create_brush()

    def create_pen(self):
        self.pen = QtGui.QPen()
        self.pen.setColor(QtCore.Qt.red)

    def create_brush(self):
        self.brush = QtGui.QBrush()
        self.brush.setColor(QtCore.Qt.blue)
        self.brush.setStyle(QtCore.Qt.CrossPattern)

    def show_text_toolbar(self):
        self.text_toolbar.show()
        self.text_toolbar.setGeometry(0, 0, self.width(), 40)

    def hide_text_toolbar(self):
        self.text_toolbar.hide()

    def update_font(self):
        font = self.text_toolbar.font_family.currentFont()
        font.setPointSize(int(self.text_toolbar.font_size.currentText()))
        font.setBold(self.text_toolbar.bold_button.isChecked())
        font.setItalic(self.text_toolbar.italic_button.isChecked())
        font.setUnderline(self.text_toolbar.underline_button.isChecked())
        self.current_font = font
        if self.current_text_item:
            self.current_text_item.setFont(font)
            self.current_text_item.setDefaultTextColor(self.text_color)

    def start_text_input(self, pos):
        clicked_item = self.scene().itemAt(self.mapToScene(pos), QtGui.QTransform())
        if isinstance(clicked_item, QtWidgets.QGraphicsTextItem):
            self.current_text_item = clicked_item
            self.current_text_item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            self.current_text_item.setFocus()
        else:
            if self.current_text_item:
                self.finalize_text_input()
            
            self.current_text_item = QtWidgets.QGraphicsTextItem()
            self.current_text_item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            self.current_text_item.setPos(self.mapToScene(pos))
            self.current_text_item.setFont(self.current_font)
            self.current_text_item.setDefaultTextColor(self.text_color)  # Use the current text color
            self.scene().addItem(self.current_text_item)
            self.current_text_item.setFocus()

    def finalize_text_input(self):
        if self.current_text_item:
            if self.current_text_item.toPlainText().strip() == "":
                self.scene().removeItem(self.current_text_item)
            else:
                self.current_text_item.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
                self.execute_command(AddItemCommand(self.scene(), self.current_text_item))
            self.current_text_item = None

    def execute_command(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
    
    def undo(self):
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            self.scene().update()

    def redo(self):
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            self.scene().update()

    def start_polygon(self, pos):
        if not self.drawing_polygon:
            self.drawing_polygon = True
            self.current_polygon = [self.mapToScene(pos)]
        else:
            if self.is_near_start_point(self.mapToScene(pos)):
                self.finish_polygon()
            else:
                self.current_polygon.append(self.mapToScene(pos))
        self.update()

    def is_near_start_point(self, point):
        if len(self.current_polygon) > 2:
            start = self.current_polygon[0]
            return (start.x() - 5 <= point.x() <= start.x() + 5 and
                    start.y() - 5 <= point.y() <= start.y() + 5)
        return False

    def finish_polygon(self):
        if len(self.current_polygon) > 2:
            self.current_polygon.append(self.current_polygon[0])  # Close the polygon
            polygon_item = QtWidgets.QGraphicsPolygonItem(QtGui.QPolygonF(self.current_polygon))
            polygon_item.setPen(self.pen)
            #polygon_item.setBrush(self.brush)
            self.execute_command(AddItemCommand(self.scene(), polygon_item))
            self.polygons.append(polygon_item)
        self.current_polygon = []
        self.drawing_polygon = False
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())
        painter.setPen(self.pen)

        # Draw the current polygon
        if len(self.current_polygon) > 1:
            for i in range(len(self.current_polygon) - 1):
                painter.drawLine(self.mapFromScene(self.current_polygon[i]), self.mapFromScene(self.current_polygon[i + 1]))

        # Draw a line from the last point to the cursor for real-time feedback
        if self.drawing_polygon and len(self.current_polygon) > 0:
            painter.drawLine(self.mapFromScene(self.current_polygon[-1]), self.mapFromGlobal(QtGui.QCursor.pos()))
    # Events
    def mousePressEvent(self, event):
        if self.tool == "text" and self.current_text_item:
            self.finalize_text_input()
        
        self.begin = self.end = event.pos()
        if self.scene():
            if self.tool == "polygon":
                # Check if we need to start or finish the polygon
                point = self.mapToScene(event.pos())
                
                if not self.current_polygon:  # Starting a new polygon
                    self.current_polygon.append(point)
                else:
                    # Check if the new point is close to the starting point
                    if self.is_near_start_point(point):
                        self.finish_polygon()  # Finish the polygon if clicked near the start point
                    else:
                        self.current_polygon.append(point)
                        # Draw the line segment to connect points
                        last_point = self.current_polygon[-2]
                        new_line = QtWidgets.QGraphicsLineItem(QtCore.QLineF(last_point, point))
                        new_line.setPen(self.pen)
                        self.scene().addItem(new_line)

                # Force the scene to update immediately
                self.update()
            elif self.tool == "select":
                clicked_item = self.scene().itemAt(self.mapToScene(self.begin), QtGui.QTransform())
                if clicked_item:
                    if event.modifiers() & QtCore.Qt.ControlModifier:
                        # Toggle selection with Ctrl key
                        if clicked_item in self.selected_items:
                            self.selected_items.remove(clicked_item)
                            clicked_item.setSelected(False)
                        else:
                            self.selected_items.append(clicked_item)
                            clicked_item.setSelected(True)
                    else:
                        # If clicked item is not in selection, clear previous selection
                        if clicked_item not in self.selected_items:
                            for item in self.selected_items:
                                item.setSelected(False)
                            self.selected_items = []
                        self.selected_items.append(clicked_item)
                        clicked_item.setSelected(True)
                    
                    self.dragging = True
                    self.drag_start_pos = self.mapToScene(event.pos())
                    self.item_original_positions = {item: item.pos() for item in self.selected_items}
                else:
                    # Clear selection if clicking on empty space
                    for item in self.selected_items:
                        item.setSelected(False)
                    self.selected_items = []
                    # Start rubber band selection
                    self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
                    self.rubberBand.setGeometry(QtCore.QRect(self.begin, QtCore.QSize()))
                    self.rubberBand.show()
            elif self.tool == "text":
                self.start_text_input(event.pos())
            elif self.tool in ["pen","line", "rectangle"]:
                self.start_drawing(event.pos())
            self.highlight_selected_items()
        else:
            print("View needs a scene to display items!")

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        if self.scene():
            if self.drawing_polygon:
                if self.temp_item:
                    self.scene().removeItem(self.temp_item)
                
                # Create a temporary line from the last polygon point to the current mouse position
                last_point = self.current_polygon[-1]
                current_pos = self.mapToScene(event.pos())
                self.temp_item = self.scene().addLine(QtCore.QLineF(last_point, current_pos), self.pen)
                
                # Update the scene to reflect changes
                self.update()
            elif self.tool == "pen" and self.current_path:
                self.current_path.lineTo(self.mapToScene(event.pos()))
                self.scene().removeItem(self.temp_item)
                self.temp_item = self.scene().addPath(self.current_path, self.pen)
            elif self.dragging and self.selected_items and self.tool == "select":
                current_pos = self.mapToScene(event.pos())
                delta = current_pos - self.drag_start_pos
                for item in self.selected_items:
                    item.setPos(self.item_original_positions[item] + delta)
            elif self.rubberBand:
                self.rubberBand.setGeometry(QtCore.QRect(self.begin, event.pos()).normalized())
            elif self.temp_item:
                self.update_temp_item(event.pos())
            self.viewport().update()
        else:
            print("View needs a scene to display items!")

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        if self.scene():
            if self.tool == "pen":
                if self.current_path:
                    final_path_item = QtWidgets.QGraphicsPathItem(self.current_path)
                    final_path_item.setPen(QtGui.QPen(self.pen))
                    self.execute_command(AddItemCommand(self.scene(), final_path_item))
                self.current_path = None
                self.temp_item = None
            elif self.dragging and self.selected_items and self.tool == "select":
                self.dragging = False
                for item in self.selected_items:
                    old_pos = self.item_original_positions[item]
                    new_pos = item.pos()
                    self.execute_command(MoveItemCommand(item, old_pos, new_pos))
                self.drag_start_pos = None
                self.item_original_positions.clear()
            elif self.rubberBand:
                rect = self.rubberBand.geometry()
                self.rubberBand.hide()
                self.rubberBand = None
                self.select_items_in_rect(rect)
            elif self.temp_item:
                self.finalize_drawing()
        else:
            print("View needs a scene to display items!")
        self.highlight_selected_items()

    def keyPressEvent(self, event):
        if self.tool == "text" and self.current_text_item and event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
            self.finalize_text_input()
        else:
            super().keyPressEvent(event)

    def start_drawing(self, pos):
        if self.tool == "pen":
            self.current_path = QtGui.QPainterPath()
            self.current_path.moveTo(self.mapToScene(pos))
            self.temp_item = self.scene().addPath(self.current_path, self.pen)
        elif self.tool == "line":
            self.temp_item = QtWidgets.QGraphicsLineItem(QtCore.QLineF(self.mapToScene(pos), self.mapToScene(pos)))
            self.temp_item.setPen(self.pen)
        elif self.tool == "rectangle":
            self.temp_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(self.mapToScene(pos), QtCore.QSizeF()))
            self.temp_item.setPen(self.pen)
            self.temp_item.setBrush(self.brush)
        
        if self.temp_item:
            self.scene().addItem(self.temp_item)

    def update_temp_item(self, pos):
        if self.temp_item:
            if isinstance(self.temp_item, QtWidgets.QGraphicsLineItem):
                self.temp_item.setLine(QtCore.QLineF(self.mapToScene(self.begin), self.mapToScene(pos)))
            elif isinstance(self.temp_item, QtWidgets.QGraphicsRectItem):
                self.temp_item.setRect(QtCore.QRectF(self.mapToScene(self.begin), self.mapToScene(pos)).normalized())

    def finalize_drawing(self):
        if self.temp_item:
            self.scene().removeItem(self.temp_item)
            if isinstance(self.temp_item, QtWidgets.QGraphicsLineItem):
                final_item = QtWidgets.QGraphicsLineItem(self.temp_item.line())
                final_item.setPen(self.pen)
            elif isinstance(self.temp_item, QtWidgets.QGraphicsRectItem):
                final_item = QtWidgets.QGraphicsRectItem(self.temp_item.rect())
                final_item.setPen(self.pen)
                final_item.setBrush(self.brush)
            elif isinstance(self.temp_item, QtWidgets.QGraphicsPathItem):
                final_item = QtWidgets.QGraphicsPathItem(self.temp_item.path())
                final_item.setPen(self.pen)
            elif isinstance(self.temp_item, QtWidgets.QGraphicsPolygonItem):
                final_item = QtWidgets.QGraphicsPolygonItem(self.temp_item.polygon())
                final_item.setPen(self.pen)
                final_item.setBrush(self.brush)  # Apply brush for polygons
            else:
                return  # If it's not a recognized item, don't add it
            self.execute_command(AddItemCommand(self.scene(), final_item))
            self.temp_item = None
            
            # Update the scene and viewport to force a redraw
            self.scene().update()  # Ensures scene is updated
            self.viewport().update()  # Forces a redraw of the vi


    def highlight_selected_items(self):
        for item in self.scene().items():
            if item in self.selected_items:
                if isinstance(item, (QtWidgets.QGraphicsLineItem, QtWidgets.QGraphicsRectItem, QtWidgets.QGraphicsPathItem)):
                    if item not in self.original_colors:
                        self.original_colors[item] = item.pen()
                    highlight_pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashLine)
                    item.setPen(highlight_pen)
                elif isinstance(item, QtWidgets.QGraphicsTextItem):
                    # Do not change the color of text items when selected
                    pass
            else:
                self.restore_item_color(item)
    
    def restore_item_color(self, item):
        if item in self.original_colors:
            if isinstance(item, (QtWidgets.QGraphicsLineItem, QtWidgets.QGraphicsRectItem, QtWidgets.QGraphicsPathItem)):
                item.setPen(self.original_colors[item])
            del self.original_colors[item]

    def select_items_in_rect(self, rect):
        self.selected_items = []
        for item in self.scene().items():
            if rect.intersects(self.mapFromScene(item.sceneBoundingRect()).boundingRect()):
                self.selected_items.append(item)
                item.setSelected(True)


    def resizeEvent(self, event):
            super().resizeEvent(event)
            if self.tool == "text":
                self.text_toolbar.setGeometry(0, 0, self.width(), 40)
            print("View.resizeEvent()")
            print("width : {}, height : {}".format(self.size().width(), self.size().height()))

if __name__ == "__main__":  
    app = QtWidgets.QApplication(sys.argv)

    # View
    x, y = 0, 0
    w, h = 600, 400
    view = View(position=(x,y), dimension=(w,h))
    view.setWindowTitle("CAI 2425 A  : View")

    # Scene
    model = QtWidgets.QGraphicsScene()
    model.setSceneRect(x, y, w, h)
    view.setScene(model)

    view.show()
    sys.exit(app.exec_())