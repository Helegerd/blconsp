# Coding:utf-8
# штука, которая читает и записывает инфу из blconsp файлов
import sys, ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QDesktopWidget, QFileDialog, QWidget
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
        
        

    def setText(self, text):
        self.text = text




class Communicate(QObject):
    '''если правильно понял, помогает установить связь меж окном и виджетом'''
    updateBW = pyqtSignal
    
    
class PieceWid(QWidget):
    '''выводит кусок с должным отступом и символом в начале'''
    def __init__(self):
        super().__init__()
    

class ConspWindowForm(QMainWindow):
    '''интерфейс для открытия и создания конспектов'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Конспекты по блокам')
        self.conspFileName = ''  # имя рассматриваемого файла с конспектом
        self.consparr = []
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
        self.readlyst = [winsizes[0] // 100 * 30, winsizes[1] // 100 * 2, winsizes[0] // 100 * 40, winsizes[1] // 100 * 96] + [QPushButton(self) for _i in range(2)]
        self.readlyst[4].setText(chr(127968))  # кнопка возврата в главное меню
        self.readlyst[4].hide()
        self.readlyst[4].resize(int(self.readlyst[2] / 100 * 4.5), int(self.readlyst[3] / 100 * 4.5))
        self.readlyst[4].move(int(self.readlyst[2] / 100 * 0.5), int(self.readlyst[3] / 100 * 0.5))
        self.readlyst[4].clicked.connect(self.changeReadToMain)
        self.readlyst[4].setFont(QFont('Arial', int(self.readlyst[2] // 100 * 2.5)))
        self.readlyst[5].setText(chr(128194))  # кнопка для открытия нового конспекта
        self.readlyst[5].hide()
        self.readlyst[5].resize(int(self.readlyst[2] / 100 * 4.5), int(self.readlyst[3] / 100 * 4.5))
        self.readlyst[5].move(int(self.readlyst[2] / 100 * 95), int(self.readlyst[3] // 100 * 0.5))
        self.readlyst[5].setFont(QFont('Arial', int(self.readlyst[2] / 100 * 2)))
        self.readlyst[5].clicked.connect(self.getConspFileName)

                
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
        try:
            self.consparr = getConspParams(self.conspFileName)
        except:
            pass
            
    def changeReadToMain(self):
        self.changeWindow(self.mainlyst, self.readlyst)
        
    def changeMainToRead(self):
        self.changeWindow(self.readlyst, self.mainlyst)
            
        
#with open('consp.blconsp', mode='wb') as conspf:
#    conspf.write(b'\xd0\x91\xd0\xb0\xd0\xb9\xd1\x82\xd1\x8b\x03\xd0\x91\x04\xd0\xb0\x04\x04\xd0\xb0\x05\xd0\xb0\x05\x04\x03')
setConspParams('consp.blconsp', params=['(5,10,)Ария',
                                        ['(5,10,)История создания', ['(5,10,☆)1985']],
                                        ['(5,10,)Лучшие песни📂', ['(5,10,☆)Точка невозврата'], ['(5,10,☆)Ночь короче дня']]])
print(getConspParams('consp.blconsp'))
runapp()
