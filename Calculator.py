#python3
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import  QApplication, QPushButton, QWidget, QLineEdit
from queue import Queue
from abc import ABCMeta, abstractmethod

class ICalDec(metaclass=ABCMeta):
    @abstractmethod
    def expression(self, s:str):
        raise NotImplementedError
    @abstractmethod
    def getResult(self) -> str:
        raise NotImplementedError

class CalUI(QWidget):
    def __init__(self):
        super(CalUI, self).__init__(None,Qt.WindowCloseButtonHint)
        self.line_edit = QLineEdit(self)
        self.butten_list = [QPushButton(self) for i in range(20)]
        self.dec = None              #计算模块接口

        self.edit_init()
        self.button_init()

    def edit_init(self):
        self.line_edit.move(10, 10)
        self.line_edit.resize(240, 30)
        self.line_edit.setReadOnly(True)
        self.line_edit.setAlignment(Qt.AlignRight)

    def button_init(self):
        context_list = ["7", "8", "9", "+", "(",
                     "4", "5", "6", "-", ")",
                     "1", "2", "3", "*", "<-",
                     "0", ".", "=", "/", "C"]

        for i in range(4):
            for j in range(5):
                self.butten_list[5*i+j].move(10+50*j,50+50*i)
                self.butten_list[5*i+j].resize(40, 40)
                self.butten_list[5*i+j].setText(context_list[5*i+j])
                self.butten_list[5*i+j].clicked.connect(self.onButtonClicked)

    def setDec(self, dec:ICalDec):
        if self.dec is None:
            self.dec = dec

    def show(self):
        super(CalUI, self).show()
        self.setFixedSize(self.width(), self.height())

    def onButtonClicked(self):
        click_btn = self.sender()
        click_text = click_btn.text()
        edit_text = self.line_edit.text()
        if click_text == 'C':
            self.line_edit.setText("")
        elif click_text == '<-':
            if len(edit_text) > 0:
                self.line_edit.setText(edit_text[:-1])
        elif click_text == '=':
            if self.dec is not None:
                try:
                    self.dec.expression(edit_text)
                    self.line_edit.setText(self.dec.getResult())
                except Exception as e:
                    print(e)
        else:
            self.line_edit.setText(edit_text + click_text)

class CalDec(ICalDec):
    def __init__(self):
        self.exp = ""
        self.result = ""
    def expression(self, s:str):
        self.exp = s
        q = self.split()
        out_q = Queue()
        self.transform(q, out_q)
        self.calculate(out_q)
    def getResult(self):
        return self.result
    def isDigitOrDot(self, s):
        return s.isdigit() or s == '.'
    def isSymbol(self, s):
        return self.isOperator(s) or s == '(' or s == ')'
    def isSign(self, s):
        return s == '+' or s == '-'
    def isOperator(self, s):
        return s == '+' or s == '-' or s == '*' or s == '/'
    def isLeft(self, s):
        return s == '('
    def isRight(self, s):
        return s == ')'
    def isNumber(self, s):
        try:
            if s == 'NaN':
                return False
            float(s)
            return True
        except ValueError:
            return False
    #分离
    def split(self) -> Queue:
        q = Queue()
        num = ""
        pre = ""
        for s in self.exp:
            if self.isDigitOrDot(s):
                num += s
                pre = s
            elif self.isSymbol(s):
                if num != "":
                    q.put(num)
                    num = ""
                if self.isSign(s) and ( pre == "" or self.isLeft(pre) or self.isOperator(pre) ):
                    num += s
                else:
                    q.put(s)
                pre = s
        if num != "":
            q.put(num)
        return q

    #判断运算符优先级
    def priority(self, s):
        ret = 0
        if s == '+' or s == '-':
            ret = 1
        elif s == '*' or s == '/':
            ret = 2
        return ret

    #判断括号匹配
    def isMatch(self, q):
        l = list(q.queue)
        stack = []
        for s in l:
            if self.isLeft(s):
                stack.append(s)
            elif self.isRight(s):
                if len(stack) != 0:
                    stack.pop()
                else:
                    return False
        if len(stack) != 0:
            return False
        else:
            return True
    #中缀转后缀
    def transform(self, input_q:Queue, output_q:Queue) -> bool:
        ret = self.isMatch(input_q)
        stack = []
        l = list(input_q.queue)
        for s in l:
            if self.isNumber(s):
                output_q.put(s)
            else:
                if len(stack) == 0:
                    stack.append(s)
                else:
                    if self.isLeft(s):
                        stack.append(s)
                    elif self.isRight(s):
                        while len(stack)!=0 and not self.isLeft(stack[-1]):
                            output_q.put(stack.pop())
                        if len(stack) != 0 :
                            stack.pop()
                    elif self.isOperator(s):
                        while len(stack)!=0 and self.priority(s) <= self.priority(stack[-1]):
                            output_q.put(stack.pop())
                        stack.append(s)
                    else:
                        ret = False
        while len(stack) != 0:
            output_q.put(stack.pop())
        if ret is False:
            output_q.queue.clear()
        return ret
    #后缀计算
    def inner_calculate(self, left_str, op, right_str):
        ret = ""
        if not self.isNumber(left_str) or not self.isNumber(right_str):
            ret = "Error!"
        else:
            l = float(left_str)
            r = float(right_str)
            if op == '+':
                ret = str(l+r)
            elif op == '-':
                ret = str(l-r)
            elif op == '*':
                ret = str(l*r)
            elif op == '/':
                try:
                    ret = str(l/r)
                except ZeroDivisionError:
                    ret = "Error!"
            else:
                ret = "Error!"
        return ret

    def calculate(self, output_q:Queue):
        stack = []
        while not output_q.empty():
            s = output_q.get()
            if self.isNumber(s):
                stack.append(s)
            elif self.isOperator(s):
                if len(stack) > 1:
                    right_str = stack.pop()
                    left_str = stack.pop()
                    op = s
                    res = self.inner_calculate(left_str, op, right_str)
                    stack.append(res)
                else:
                    self.result = "Error!"
            else:
                self.result = "Error!"
        if len(stack) == 1:
            self.result = stack.pop()
        else:
            self.result = "Error!"

class Calculator(object):
    def __init__(self):
        self.ui = CalUI()
        self.cal = CalDec()
        self.setCal()
    #绑定计算模块到UI
    def setCal(self):
        self.ui.setDec(self.cal)
    def show(self):
        self.ui.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    c = Calculator()
    c.show()
    sys.exit(app.exec_())
