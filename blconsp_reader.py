# Coding:utf-8
# штука, которая читает и записывает инфу из blconsp файлов
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QDesktopWidget
from PyQt5.QtGui import QFont
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

def getConspParams(conspfile):
    '''возвращает структуру конспекта в виде списка'''
    decoding = 'utf-8'
    params = ['']
    depthlayer = 0  # насколько низко опустилсь по структуре
    with open(conspfile, mode='rb') as conspf:
        hhead = ''  # название конспекта считывается сыда и записывается в общий словарь
        headtext = ''  # для текущего заголовка
        blocktext = ''  # для текущей блока
        notetext = ''  # для текущей записи
        unotetext = ''  # для текущей подзаписи
        headnum = 0  # номер заголовка
        blocknum = 0
        notenum = 0
        unotenum = 0
        b = b''  # переменная для считывания байтов
        while True:  # считывание заголовка
            b = conspf.read(1)
            if b in (b'', b'\x03', b'\x05', b'\x04', b'\x06'):
                conspf.seek(-1, 1)
                break
            for _i in range(octnum(b) - 1):
                b = b + conspf.read(1)
            hhead = hhead + b.decode('utf-8')
        params[0] = hhead  # запись названия конспекта
        while True:  # считывание прочего
            b = conspf.read(1)
            if b == b'':
                break
              # проверка на некорректность файла ниже
              # сомневаюсь, нужно ли
            if b == b'\x03' and depthlayer not in (0, 1) or\
               b == b'\x04' and depthlayer not in (1, 2) or\
               b == b'\x05' and depthlayer not in (2, 3) or\
               b == b'\x06' and depthlayer not in (3, 4):
                return('Error in reading')
            if b == b'\x03':  # начало/конец заголовка
                if depthlayer == 0: # если уровень выше на 1
                    depthlayer += 1
                    params.append([''])
                    headnum += 1
                elif depthlayer == 1:  # если на уровне этого куска
                    params[headnum][0] = headtext  # запись названия куска
                    blocknum = 0  # обнуление кусков на приоритет ниже
                    depthlayer -= 1
                    headtext = ''
            elif b == b'\x04':  # начало/конец блока
                if depthlayer == 1:
                    depthlayer += 1
                    params[headnum].append([''])
                    blocknum += 1
                elif depthlayer == 2:
                    params[headnum][blocknum][0] = blocktext
                    notenum = 0
                    depthlayer -= 1
                    blocktext = ''
            elif b == b'\x05':  # начало/конец записи
                if depthlayer == 2:
                    depthlayer += 1
                    params[headnum][blocknum].append([''])
                    notenum += 1
                elif depthlayer == 3:
                    params[headnum][blocknum][notenum][0] = notetext
                    depthlayer -= 1
                    unotenum = 0
                    notetext = ''
            elif b == b'\x06':  # начало/конец подзаписи
                if depthlayer == 3:
                    depthlayer += 1
                    params[headnum][blocknum][notenum].append([''])
                    unotenum += 1
                elif depthlayer == 4:
                    params[headnum][blocknum][notenum][unotenum][0] = notetext
                    depthlayer -= 1
                    notetext = ''
            elif depthlayer == 1:  # приращение заголовка
                for _i in range(octnum(b) - 1):
                    b = b + conspf.read(1)
                headtext = headtext + b.decode('utf-8')
            elif depthlayer == 2:  # приращение блока
                for _i in range(octnum(b) - 1):
                    b = b + conspf.read(1)
                blocktext = blocktext + b.decode('utf-8')
            elif depthlayer == 3:  # приращение записи
                for _i in range(octnum(b) - 1):
                    b = b + conspf.read(1)
                notetext = notetext + b.decode('utf-8')
            elif depthlayer == 4:  # приращение подзаписи
                for _i in range(octnum(b) - 1):
                    b = b + conspf.read(1)
                unotetext = unotetext + b.decode('utf-8')
    
        return params
        
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
        
        
    def changeWindow(towin, fromwin, self):
        '''меняет окна'''
        for widget in fromwin[4:]:
            widget.hide()
        self.setFixedSize(towin[2], towin[3])
        self.move(towin[0], towinp[1])
        for widget in tomwin[4:]:
            widget.show()
            
        
#with open('consp.blconsp', mode='wb') as conspf:
#    conspf.write(b'\xd0\x91\xd0\xb0\xd0\xb9\xd1\x82\xd1\x8b\x03\xd0\x91\x04\xd0\xb0\x04\x04\xd0\xb0\x05\xd0\xb0\x05\x04\x03')
setConspParams('consp.blconsp', params=['Ария', ['История создания', ['1985']], ['Лучшие песни', ['Точка невозврата'], ['Ночь короче дня']]])
print(getConspParams('consp.blconsp'))
runapp()
