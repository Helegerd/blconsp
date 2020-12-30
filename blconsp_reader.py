# Coding:utf-8
# штука, которая читает и записывает инфу из blconsp файлов
import sys, ctypes
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal
winsizes = (190, 180)
layerbytes = [b'', b'\x03', b'\x04', b'\x05', b'\x06']


def octnum(firstoct=b'\xd0'):
    '''возвращает кол-во октетов, анализируя первый
    нужно для удобства при чтении байтов'''
    decnum = firstoct[0]
    binnum = bin(decnum)
    if len(binnum) < 10:
        return 1
    if binnum[2:5] == '110':
        return 2
    if binnum[2:6] == '1110':
        return 3
    if binnum[2:7] == '11110':
        return 4

def getConspParams(conspFileName):
    '''возвращает структуру конспекта в виде списка'''
    global layerbytes
    with open(conspFileName, mode='rb') as conspfile:
        def getListParams(f, depthLayer=0):
            retlist = ['']  # список для возвратра
            while True:
                byte = f.read(1)  # текущий считываемый байт
                if byte == layerbytes[depthLayer]:  # конец ли этого куска
                    return retlist
                elif byte == layerbytes[depthLayer + 1]:  # начало ли следующего куска
                    retlist.append(getListParams(f, depthLayer=depthLayer + 1))
                else:
                    for _i in range(octnum(byte) - 1):
                        byte = byte + f.read(1)
                    retlist[0] = retlist[0] + byte.decode('utf-8')
        return getListParams(conspfile)
        
def setConspParams(conspFileName, params=[], depthlayer=0):
    '''записывает конспект в файл с именем conspFileName,
    считывая данные из списка params
    depthlayer нужен для рекурсии'''
    global layerbytes
    retbyte = params[0].encode('utf-8')  # шифровка текста
    if len(params) > 1:
        for piece in params[1:]:
            retbyte = retbyte + layerbytes[depthlayer + 1] +\
                setConspParams(conspFileName, params=piece, depthlayer=depthlayer + 1) +\
                layerbytes[depthlayer + 1]
    if depthlayer == 0:
        with open(conspFileName, mode='wb') as conspf:
            conspf.write(retbyte)
    return retbyte

def runapp():
    '''запуск окна
    в функции, чтобы не было проблем при импорте'''
    global winsizes
    if __name__ == '__main__':
        app = QApplication(sys.argv)
        q = QDesktopWidget().availableGeometry()  # для считывания размеров экрана
        winsizes = (q.width(), q.height())  # для записи размеров экрана
        consp = ConspWindowForm()
        consp.show()
        sys.exit(app.exec_())
    

class ConspWindowForm(QMainWindow):
    '''интерфейс для открытия и создания конспектов'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Конспекты по блокам')
        self.conspFileName = ''  # имя рассматриваемого файла с конспектом
        self.consparr = []  # содержимое конспекта ввиде списка
        self.conspIsOpen = False
        # структура списка окна:
        # [x_отступа, у_отступа, х размера, у размера, виджет1, виджет 2, ...]

        # стартовое окно
        self.mainlyst = [winsizes[0] // 4, winsizes[1] // 4, winsizes[0] // 2, winsizes[1] // 2, QPushButton(self), QPushButton(self), QPushButton(self), QPushButton(self)]
        self.move(self.mainlyst[0], self.mainlyst[1])
        self.setFixedSize(self.mainlyst[2], self.mainlyst[3])
        self.mainlyst[4].setText(chr(128214))  # кнопка, открывает конспектный файл
        self.mainlyst[4].resize(self.mainlyst[2] // 100 * 35, self.mainlyst[3] // 100 * 35)
        self.mainlyst[4].move(int(self.mainlyst[2] // 100 * 10.5), int(self.mainlyst[3] // 100 * 10.5))
        self.mainlyst[4].setFont(QFont('Arial', self.mainlyst[3] // 100 * 16))
        self.mainlyst[4].clicked.connect(self.changeMainToRead)
        self.mainlyst[5].setText('+')  # кнопка для создания конспекта
        self.mainlyst[5].resize(self.mainlyst[2] // 100 * 35, self.mainlyst[3] // 100 * 35)
        self.mainlyst[5].move(int(self.mainlyst[2] // 100 * 54.5), int(self.mainlyst[3] // 100 * 10.5))
        self.mainlyst[5].setFont(QFont('Arial', self.mainlyst[3] // 100 * 35 - 1))
        self.mainlyst[6].setText(chr(128218))  # кнопка для перехода к библиотеке папок конспектов
        self.mainlyst[6].resize(self.mainlyst[2] // 100 * 35, self.mainlyst[3] // 100 * 35)
        self.mainlyst[6].move(int(self.mainlyst[2] // 100 * 10.5), int(self.mainlyst[3] // 100 * 54.5))
        self.mainlyst[6].setFont(QFont('Arial', self.mainlyst[3] // 100 * 16))
        self.mainlyst[7].setText(chr(9881))  # для открытия окна с настройками
        self.mainlyst[7].resize(self.mainlyst[2] // 100 * 35, self.mainlyst[3] // 100 * 35)
        self.mainlyst[7].move(int(self.mainlyst[2] // 100 * 54.5), int(self.mainlyst[3] // 100 * 54.5))
        self.mainlyst[7].setFont(QFont('Arial', self.mainlyst[3] // 100 * 16))
        
        # окно чтения конспектов
        self.readlyst = [winsizes[0] // 100 * 30, winsizes[1] // 100 * 2, winsizes[0] // 100 * 40, winsizes[1] // 100 * 96] + [QPushButton(self) for _i in range(3)]
        self.readlyst[4].setText(chr(127968))  # кнопка возврата в главное меню
        self.readlyst[4].hide()
        self.readlyst[4].resize(int(self.readlyst[2] / 100 * 4.5), int(self.readlyst[3] / 100 * 4.5))
        self.readlyst[4].move(int(self.readlyst[2] / 100 * 95.5), int(self.readlyst[3] // 100 * 0.5))
        self.readlyst[4].clicked.connect(self.changeReadToMain)
        self.readlyst[4].setFont(QFont('Arial', int(self.readlyst[2] // 100 * 2.5)))
        self.readlyst[5].setText(chr(128194))  # кнопка для открытия нового конспекта
        self.readlyst[5].hide()
        self.readlyst[5].resize(int(self.readlyst[2] / 100 * 4.5), int(self.readlyst[3] / 100 * 4.5))
        self.readlyst[5].move(int(self.readlyst[2] / 100 * 95.5), int(self.readlyst[3] // 100 * 5.5))
        self.readlyst[5].setFont(QFont('Arial', int(self.readlyst[2] / 100 * 2)))
        self.readlyst[5].clicked.connect(self.getConspFileName)
        self.readlyst[6].hide()  # сохранить конспект как
        self.readlyst[6].setText('🖫')
        self.readlyst[6].resize(int(self.readlyst[2] / 100 * 4.5), int(self.readlyst[3] / 100 * 4.5))
        self.readlyst[6].move(int(self.readlyst[2] / 100 * 95.5), int(self.readlyst[3] // 100 * 10.5))
        self.readlyst[6].setFont(QFont('Arial', int(self.readlyst[2] / 100 * 2)))
        self.readlyst[6].clicked.connect(self.changeBords)
        self.piecelist = []  # виджеты, воплощающие куски [[begsymbollab1, textEdit1], [begsymbollab2, textEdit2], ...]
        self.begWid = 0
        self.endWid = 0  # начальный и конечный виджеты
        

                
    def changeWindow(self, towin, fromwin):
        '''меняет окна'''
        for widget in fromwin[4:]:
            widget.hide()
        self.setFixedSize(towin[2], towin[3])
        self.move(towin[0], towin[1])
        for widget in towin[4:]:
            widget.show()
            
    def getConspFileName(self):
        '''пользователь показывает на файл с конспектом'''
        self.conspFileName = QFileDialog.getOpenFileName(self, 'Выберете конспект', '', 'Конспект(*.blconsp)')[0]
        self.consparr = getConspParams(self.conspFileName)
        self.yPosMove = 0  # для нормального смещения кусков
        def getWids(consparr, depth=-1):  # запсь виджетов в self.piecelist
            self.piecelist.append([QLabel(self), QTextEdit(self)])
            datas = ['', '', '']  # [у размер в %, размер шрифта, начальный символ]
            index = 0  # для ориентировки в datas
            text = consparr[0].split(')')[1]  # для установки в QTextEdit
            for sym in consparr[0].split(')')[0][1:]:
                if sym == ',':
                    index += 1
                    continue
                datas[index] = datas[index] + sym
            d = depth  # чтобы объединить случаи с верховным заголовком и заголовком
            if depth == -1:
                d += 1
            # лабел с маркой
            self.piecelist[-1][0].setText(datas[2])
            self.piecelist[-1][0].resize(int(self.width() * d * 0.05), int(self.height() * int(datas[0]) / 100))
            self.piecelist[-1][0].move(int(self.width() * d * 0.05), self.yPosMove)
            self.piecelist[-1][0].show()
            # сам кусок
            self.piecelist[-1][1].setText(text)
            self.piecelist[-1][1].resize(int(self.width() * (0.9 - d * 0.05)), int(self.height() * int(datas[0]) / 100))
            self.piecelist[-1][1].setReadOnly(True)
            self.piecelist[-1][1].move(int(self.width() * (d + 1) * 0.05), self.yPosMove)
            self.piecelist[-1][1].setFont(QFont('Arial', int(datas[1])))
            self.piecelist[-1][1].show()
            # удлинение отступа и пробежка по более глубоким уровням
            self.yPosMove += int(self.height() * int(datas[0]) / 100 + self.height() * 0.01)
            if len(consparr) > 1:
                for wid in consparr[1:]:
                    getWids(wid, depth=depth + 1)
        getWids(self.consparr)
        self.conspIsOpen = True
    
    def changeBords(self):
        '''пересматривает то, какие виджеты видны в экране
        нужно для оптимизации взаимодействия с ними
        movement = -1/1 -- направление смещающихся вниз/вверх виджетов'''
        lenthPiece = len(self.piecelist) - 1
        if self.conspIsOpen:
            if self.piecelist[self.begWid][1].height() + self.piecelist[self.begWid][1].y() >= 0:  # для определения самого высокого виджета на экране
                while not (self.begWid == 0 or self.piecelist[self.begWid][1].height() + self.piecelist[self.begWid][1].y() < 0):
                    self.begWid -= 1
                if self.piecelist[self.begWid][1].height() + self.piecelist[self.begWid][1].y() < 0:
                    self.begWid += 1
            elif self.piecelist[self.begWid][1].height() + self.piecelist[self.begWid][1].y() < 0:
                while self.piecelist[self.begWid][1].height() + self.piecelist[self.begWid][1].y() < 0:
                    self.begWid += 1
            if self.piecelist[self.endWid][1].y() > self.height():  # для определения самого низкого виджета на экране
                while self.endWid != lenthPiece or self.piecelist[self.endWid][1].y() > self.height():
                    self.endWid -= 1
            elif self.piecelist[self.endWid][1].y() <= self.height():
                while not (self.piecelist[self.endWid][1].y() > self.height() or self.endWid == lenthPiece):
                    print(self.endWid)
                    self.endWid += 1
                if self.piecelist[self.endWid][1].y() > self.height():
                    self.endWid -= 1
            print(self.begWid, self.endWid)
        
    # events
    
    def wheelEvent(self, event):
        if self.conspIsOpen:
            if self.piecelist[0][1].y() <= 0 and event.angleDelta().y() > 0:  # вверх
                ad = event.angleDelta().y()
                if ad > -1 * self.piecelist[0][1].y():
                    ad = -1 * self.piecelist[0][1].y()
                for wids in self.piecelist:
                    for wid in wids:
                        wid.move(wid.x(), wid.y() + ad)
                
            if self.piecelist[-1][1].y() >= 0 and event.angleDelta().y() < 0:  # вниз
                ad = event.angleDelta().y()
                if -1 * ad > self.piecelist[-1][1].y():
                    ad = -1 * self.piecelist[-1][1].y()
                for wids in self.piecelist:
                    for wid in wids:
                        wid.move(wid.x(), wid.y() + ad)
    
    # for screen view changing
    
    def changeReadToMain(self):
        self.changeWindow(self.mainlyst, self.readlyst)
        
    def changeMainToRead(self):
        self.changeWindow(self.readlyst, self.mainlyst)
            
        
#with open('consp.blconsp', mode='wb') as conspf:
#    conspf.write(b'\xd0\x91\xd0\xb0\xd0\xb9\xd1\x82\xd1\x8b\x03\xd0\x91\x04\xd0\xb0\x04\x04\xd0\xb0\x05\xd0\xb0\x05\x04\x03')
setConspParams('consp.blconsp', params=['(5,10,)Ария',
                                        ['(5,10,)История создания', ['(5,10,☆)1985']],
                                        ['(5,10,)Лучшие песни⇚⇛✅🖫', ['(5,10,☆)Точка невозврата'], ['(5,10,☆)Ночь короче дня']]])
print(getConspParams('consp.blconsp'))
runapp()
