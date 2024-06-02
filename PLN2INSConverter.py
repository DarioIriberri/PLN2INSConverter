# -*- coding: utf-8 -*-
__author__ = 'Dario'
import sys, os, io
import xml.etree.ElementTree as et
from PyQt5 import QtCore, QtWidgets as qtw, QtGui

class MyWidget(qtw.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Civa INS Flight Plan Converter v0.1')

        applicationPath = None
        if getattr(sys, 'frozen', False):
            applicationPath = sys._MEIPASS
        elif __file__:
            applicationPath = os.path.dirname(__file__)
        #print('applicationPath ======================= ' + applicationPath)
        self.setWindowIcon(QtGui.QIcon(os.path.join(applicationPath, "insIcon.ico")))

        self.setGeometry(900,200,300,900)

        self.fltTextBox = qtw.QPlainTextEdit()
        self.fltTextBox.setReadOnly(True)
        self.checkPartial = qtw.QCheckBox("Use 1-5 and 6-9 waypoint splits")
        self.buttonOpenPLN = qtw.QPushButton('Open and Convert PLN file')
        self.comboBoxWPxFile = qtw.QComboBox(self)
        self.comboBoxWPxFile.addItems(['9 waypoints per file', '8 waypoints per file',
                                       '7 waypoints per file', '6 waypoints per file',
                                       '5 waypoints per file', '4 waypoints per file'])
        self.comboBoxWPxFile.setCurrentIndex(2)
        self.buttonConvert = qtw.QPushButton('Save ADEU Files')

        self.statusBar = qtw.QStatusBar(self)
        self.statusBar.showMessage('No flight plan loaded.')

        self.layout = qtw.QVBoxLayout(self)
        #self.layout.addWidget(self.text)
        self.layout.addWidget(self.fltTextBox)
        self.layout.addWidget(self.buttonOpenPLN)
        self.layout.addWidget(self.checkPartial)
        self.layout.addWidget(self.comboBoxWPxFile)
        self.layout.addWidget(self.buttonConvert)
        self.layout.addWidget(self.statusBar)

        self.buttonOpenPLN.clicked.connect(self.getPLNFile)
        self.checkPartial.clicked.connect(self.checkPartialChanged)
        self.buttonConvert.clicked.connect(self.saveADEUFiles)
        self.comboBoxWPxFile.currentIndexChanged.connect(self.comboChanged)
        self.fileName = None
        self.convertedText = None
        self.numberOfBlocks = 0

        self.adeuDir = 'C:/Program Files (x86)/Microsoft Games/Microsoft Flight Simulator X/Civa/ADEU/'

    def checkPartialChanged(self):
        if self.checkPartial.isChecked():
            self.comboBoxWPxFile.setDisabled(True)
        else:
            self.comboBoxWPxFile.setDisabled(False)

        self.fltTextBox.setPlainText(self.convertPLN())
        self.updateStatusBar()

    def comboChanged(self):
        self.fltTextBox.setPlainText(self.convertPLN())
        self.updateStatusBar()

    def convertPLN(self):
        def formatCoordinate(coordinate):
            coordinate = coordinate.replace(' ', '').replace('°', '*').replace('"', '')
            parts = coordinate.split('\'')
            parts2 = parts[0].split('*')
            rose = parts2[0][0:1]
            degrees = parts2[0][1:]
            if rose == 'N' or rose == 'S':
                degrees = rose + ' ' + '%02d' % int(degrees)
            else:
                degrees = rose + ' ' + '%03d' % int(degrees)
            coordinate = degrees + '*' + '%04.1f' % (float(parts2[1]) + round(float(parts[1]) / 60,1))
            return coordinate

        if self.fileName == '' or self.fileName == None:
            return

        self.convertedText = ''
        try:
            self.departureID = self.destinationID = None
            tree = et.parse(self.fileName)
            root = tree.getroot()
            wpID = None
            wpCount = 0
            for child in root[1]:
                if child.tag.lower() == 'departureid':
                    self.departureID = child.text
                if child.tag.lower() == 'destinationid':
                    self.destinationID = child.text
                    self.convertedText += '; ' + self.departureID + ' to ' + self.destinationID + '\n\n'
                if child.tag == 'ATCWaypoint':
                    wpID = child.attrib['id']
                    for wpchild in child:
                        validWP = True
                        if wpchild.tag == 'ATCWaypointType':
                            if wpchild.text == 'Airport' or wpchild.text == 'User':
                                validWP = False
                                break
                            if not validWP: break
                            for wpchild2 in child:
                                if wpchild2.tag == 'WorldPosition':
                                    latitude = formatCoordinate(wpchild2.text.split(',')[0])
                                    longitude = formatCoordinate(wpchild2.text.split(',')[1])
                                    wpIndex = 1+(wpCount % 9)
                                    wpLine = str(wpIndex) + ' ' + latitude + ' ' + longitude + ' ; ' + wpID
                                    if self.checkPartial.isChecked():
                                        if wpCount > 7 and wpIndex in [6, 1]:
                                            self.convertedText += '\n'

                                    else:
                                        if wpCount > 0 and wpCount % self.getSelectedNumWP() == 0:
                                            self.convertedText += '\n'

                                    self.convertedText += wpLine + '\n'
                                    wpCount += 1
                                    break
        except:
            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Critical)
            msg.setText("The selected file doesn't have the expected format")
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle("Error")
            msg.exec_()

        return self.convertedText

    def getSelectedNumWP(self):
        return 9 - self.comboBoxWPxFile.currentIndex()

    def updateStatusBar(self):
        plnTxt = self.fltTextBox.toPlainText()
        statusTxt = 'No blocks found.'
        if plnTxt != None and plnTxt != '':
            statusTxt = '%d ADEU files will be created.' % (len(plnTxt.split('\n\n')) - 1)

        self.statusBar.showMessage(statusTxt)

    #@QtCore.pyqtSlot()
    def getPLNFile(self):
        self.fileName = qtw.QFileDialog.getOpenFileName(self, 'Open File',
                                       os.getenv('USERPROFILE') + '/Documents/Flight Simulator X Files',
                                       ('Text (*.pln)'))[0]

        #self.fltText=io.open(fileName[0], mode='r', encoding='utf-8').read()
        self.fltTextBox.setPlainText(self.convertPLN())
        self.updateStatusBar()
        #print(fileName)

    #@QtCore.pyqtSlot()
    def saveADEUFiles(self):
        def getBlockHeader(self, block, title, fileNumber):
            if block[0:1] == ';':
                title = block + '\n'
                return None
            self.firstWP = block.split('\n')[0].split(';')[1].replace(' ', '')
            self.lastWP = block.split(';')[len(block.split(';'))-1].replace(' ', '').replace('\n', '')
            return title + '; File #' + str(fileNumber) + ' - ' + self.firstWP + ' to ' + self.lastWP + '\n;\n'

        def saveFile(fileName, fileText, filesSaved):
            f = open(self.adeuDir + fileName, 'w')
            f.write(fileText)
            f.close()
            return filesSaved + 1

        if self.convertedText == None or self.convertedText == '':
            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Warning)
            msg.setText('Nothing to save')
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle('Warning')
            msg.exec_()

            return
        try:
            adeuDir = str(qtw.QFileDialog.getExistingDirectory(self, 'Select ADEU Directory', self.adeuDir)) + '/'
            if adeuDir == None or adeuDir == '/':
                return
            self.adeuDir = adeuDir

            fileNumber = 0
            filesSaved = 0
            title = ''
            self.convertedText.split('\n\n')
            for block in self.convertedText.split('\n\n'):
                fileText = getBlockHeader(self, block, title, fileNumber)
                if fileText == None:
                    continue
                fileNumber += 1
                fileText += block
                fileName = self.departureID + self.destinationID + ' ' + str(fileNumber) + ' ' + self.firstWP + '-' + self.lastWP +'.awc'
                filesSaved = saveFile(fileName, fileText, filesSaved)

            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Information)
            msg.setText(str(filesSaved) + ' files succesfully saved.')
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle('Success!')
            msg.exec_()
        except:
            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Critical)
            msg.setText('Something went wrong')
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle('Error')
            msg.exec_()


if __name__ == '__main__':
    app = qtw.QApplication([])

    widget = MyWidget()
    #widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())