# -*- coding: utf-8 -*-
__author__ = 'Dario'
import sys, os, io
import xml.etree.ElementTree as et
from PyQt5 import QtCore, QtWidgets, QtGui

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Civa INS Flight Plan Converter')
        self.setGeometry(900,200,300,800)

        self.fltTextBox = QtWidgets.QPlainTextEdit()
        self.fltTextBox.setReadOnly(True)

        self.buttonOpenPLN = QtWidgets.QPushButton('Open PLN and Convert')
        self.checkPartial = QtWidgets.QCheckBox("Use partial files with the first n waypoints")
        self.comboBoxPartial = QtWidgets.QComboBox()
        self.comboBoxPartial.setDisabled(True)
        self.comboBoxPartial.addItems(['1 waypoint in partial files', '2 waypoints in partial files',
                                       '3 waypoints in partial files', '4 waypoints in partial files',
                                       '5 waypoints in partial files', '6 waypoints in partial files',
                                       '7 waypoints in partial files', '8 waypoints in partial files'])
        self.comboBoxPartial.setCurrentIndex(4)
        self.buttonConvert = QtWidgets.QPushButton('Save ADEU Files')
        #self.text = QtWidgets.QLabel('Hello World', alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        #self.layout.addWidget(self.text)
        self.layout.addWidget(self.fltTextBox)
        self.layout.addWidget(self.buttonOpenPLN)
        self.layout.addWidget(self.checkPartial)
        self.layout.addWidget(self.comboBoxPartial)
        self.layout.addWidget(self.buttonConvert)

        self.buttonOpenPLN.clicked.connect(self.getPLNFile)
        self.checkPartial.clicked.connect(self.checkPartialChanged)
        self.buttonConvert.clicked.connect(self.saveADEUFiles)
        self.fileName = None
        self.convertedText = None

        self.adeuDir = 'C:/Program Files (x86)/Microsoft Games/Microsoft Flight Simulator X/Civa/ADEU/'

    def checkPartialChanged(self):
        if self.checkPartial.isChecked():
            self.comboBoxPartial.setDisabled(False)
            self.fltTextBox.setPlainText(self.convertPLN(self.fileName, 9))
        else:
            self.comboBoxPartial.setDisabled(True)
            self.fltTextBox.setPlainText(self.convertPLN(self.fileName, 8))

    def convertPLN(self, plnFileName, groupSize):
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

        if plnFileName == '' or plnFileName == None:
            return

        self.convertedText = ''
        try:
            self.departureID = self.destinationID = None
            tree = et.parse(plnFileName)
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
                                    wpLine = str(1+(wpCount % 9)) + ' ' + latitude + ' ' + longitude + ' ; ' + wpID
                                    if wpCount > 0 and wpCount % groupSize == 0:
                                        self.convertedText += '\n'
                                    self.convertedText += wpLine + '\n'
                                    wpCount += 1
                                    break
        except:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("The selected file doesn't have the expected format")
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle("Error")
            msg.exec_()

        return self.convertedText

    @QtCore.pyqtSlot()
    def getPLNFile(self):
        self.fileName = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',
                                       os.getenv('USERPROFILE') + '/Documents/Flight Simulator X Files',
                                       ('Text (*.pln)'))[0]

        #self.fltText=io.open(fileName[0], mode='r', encoding='utf-8').read()
        groupSize = 9 if self.checkPartial.isChecked() else 8
        self.fltTextBox.setPlainText(self.convertPLN(self.fileName, groupSize))
        #print(fileName)

    @QtCore.pyqtSlot()
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
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText('Nothing to save')
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle('Warning')
            msg.exec_()

            return
        try:
            adeuDir = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select ADEU Directory', self.adeuDir)) + '/'
            if adeuDir == None or adeuDir == '/':
                return
            self.adeuDir = adeuDir

            fileNumber = 0
            filesSaved = 0
            title = ''
            self.convertedText.split('\n\n')
            partialWps = self.comboBoxPartial.currentIndex() + 1
            for block in self.convertedText.split('\n\n'):
                fileText = getBlockHeader(self, block, title, fileNumber)
                if fileText == None:
                    continue
                fileNumber += 1
                fileText += block
                fileName = self.departureID + self.destinationID + ' ' + str(fileNumber) + ' ' + self.firstWP + '-' + self.lastWP +'.awc'
                filesSaved = saveFile(fileName, fileText, filesSaved)
                if self.checkPartial.isChecked() and fileNumber > 1 and len(list(filter(None, block.split('\n')))) > partialWps:
                    block = block.split('\n' + str(partialWps + 1))[0]
                    fileText = getBlockHeader(self, block, title, fileNumber)
                    fileText += block
                    fileName = self.departureID + self.destinationID + ' Part ' + str(fileNumber) + ' ' + self.firstWP + '-' + self.lastWP +'.awc'
                    filesSaved = saveFile(fileName, fileText, filesSaved)

            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            if self.checkPartial.isChecked():
                fileNumber *= 2
            msg.setText(str(filesSaved) + ' files succesfully saved.')
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle('Success!')
            msg.exec_()
        except:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText('Something went wrong')
            #msg.setInformativeText("The selected file doesn't have the expected format")
            msg.setWindowTitle('Error')
            msg.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    #widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())