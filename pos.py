#!/usr/bin/env python

import sys
from PySide2.QtWidgets import QApplication, QLabel, QMainWindow, QSizePolicy, QScrollArea
from PySide2.QtGui import QImageReader, QPixmap
from PySide2.QtCore import Qt

IMG_FILE = "/home/boris/Desktop/BehindParking/DCIM/100MEDIA/DJI_0004.JPG"


class MyScrollArea(QScrollArea):
    def __init__(self, zoomCB, clickCB, keyCB):
        QScrollArea.__init__(self)

        self.zoomCB = zoomCB
        self.clickCB = clickCB
        self.keyCB = keyCB

    def wheelEvent(self, ev):
        screen_x, screen_y = ev.x(), ev.y()
        if ev.angleDelta().y() > 0:
            self.zoomCB(screen_x, screen_y, 1.2)
        else:
            self.zoomCB(screen_x, screen_y, 0.8)

    def mousePressEvent(self, ev):
        x = self.horizontalScrollBar().value() + ev.x()
        y = self.verticalScrollBar().value() + ev.y()
        self.clickCB(x, y)

    def keyPressEvent(self, ev):
        self.keyCB(ev)


class CrossMarker(QLabel):
    SELECTED_SS = "QLabel { background-color : red; color : blue; }"
    NORMAL_SS = "QLabel { background-color : white; color : black; }"

    def __init__(self, parent, x, y):
        QLabel.__init__(self, parent)
        self.setText("???")
        self.setStyleSheet(self.SELECTED_SS)
        self.show()

        self.pixX = x
        self.pixY = y

        self.name = None
        self.overwrite_name = True

    def zoom(self, scaleFactor):
        self.move(self.pixX * scaleFactor, self.pixY * scaleFactor)

    def unselect(self):
        self.setStyleSheet(self.NORMAL_SS)

    def select(self):
        self.overwrite_name = True
        self.setStyleSheet(self.SELECTED_SS)

    def name_part(self, part):
        if self.overwrite_name:
            self.name = part
            self.overwrite_name = False
        else:
            self.name += part

        self.setText(self.name)
        self.adjustSize()


class Markers:
    def __init__(self, parent):
        self.parent_widget = parent
        self.markers = []
        self.selected = None

    def add(self, x, y, scaleFactor):
        m = CrossMarker(self.parent_widget, x, y)
        m.zoom(scaleFactor)

        self.markers.append(m)
        self.select(+1)

    def zoom(self, scaleFactor):
        for m in self.markers:
            m.zoom(scaleFactor)

    def select(self, step):
        # special case, no markers created yet
        if len(self.markers) == 0:
            return

        if self.selected is None:
            # no current selection
            self.selected = 0
        else:
            self.markers[self.selected].unselect()
            self.selected += step

        # wrap around
        if self.selected < 0:
            self.selected = len(self.markers) - 1
        elif self.selected >= len(self.markers):
            self.selected = 0

        self.markers[self.selected].select()

    def delete_selected(self):
        if self.selected is None:
            return

        self.markers[self.selected].setParent(None)
        del self.markers[self.selected]
        self.selected = None

    def name_part(self, part):
        if self.selected is None:
            return

        self.markers[self.selected].name_part(part)

    def dump(self):
        for m in self.markers:
            print("%s %s %s" % (m.name, m.pixX, m.pixY))


class KeysManager:
    def __init__(self, markers):
        self.markers = markers

    def keyEventKB(self, ev):
        key = ev.key()
        if key == Qt.Key.Key_Left:
            self.markers.select(-1)
            return
        elif key == Qt.Key.Key_Right:
            self.markers.select(+1)
            return
        elif key == Qt.Key.Key_Delete:
            self.markers.delete_selected()
            return

        text = ev.text().upper()
        if text in ["I", "V", "X"]:
            self.markers.name_part(text)
            return

        if text == "D":
            self.markers.dump()


class Viewer(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.scaleFactor = 1.0

        self.imageLabel = QLabel()
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.show()

        self.markers = Markers(self.imageLabel)

        km = KeysManager(self.markers)

        self.scrollArea = MyScrollArea(self.zoom, self.click, km.keyEventKB)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)

    def load_image(self):
        self.imageLabel.setPixmap(load_img())

        self.scrollArea.setVisible(True)
        self.imageLabel.adjustSize()

    def zoom(self, scr_x, scr_y, factor):
        #
        # figure out pixel coordinate where mouse pointer is
        #
        hsb = self.scrollArea.horizontalScrollBar()
        cur_pixel_x = (hsb.value() + scr_x) / self.scaleFactor

        vsb = self.scrollArea.verticalScrollBar()
        cur_pixel_y = (vsb.value() + scr_y) / self.scaleFactor

        #
        # rescale the image
        #
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        self.markers.zoom(self.scaleFactor)

        #
        # adjust scroll so the we zoom in/out at where we are pointing
        #
        left_pixel_x = cur_pixel_x - (scr_x / self.scaleFactor)
        hsb.setValue(left_pixel_x * self.scaleFactor)

        top_pixel_y = cur_pixel_y - (scr_y / self.scaleFactor)
        vsb.setValue(top_pixel_y * self.scaleFactor)

    def click(self, x, y):
        x /= self.scaleFactor
        y /= self.scaleFactor

        self.markers.add(x, y, self.scaleFactor)


def load_img():
    img = QImageReader(IMG_FILE).read()
    pmap = QPixmap.fromImage(img)

    return pmap


def main():
    app = QApplication([])
    viewer = Viewer()
    viewer.load_image()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
