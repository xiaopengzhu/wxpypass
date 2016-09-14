# coding:utf8

import sys
import wx
import wx.grid
import sqlite3
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex


# 主窗体
class MyFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, u"密码管理器", size=(600, 300))
        self.init_ui()

    # 绘制UI
    def init_ui(self):
        # 菜单
        menubar = wx.MenuBar()
        record_menu = wx.Menu()
        new_item = record_menu.Append(wx.NewId(), u'新建', u'打开')
        self.Bind(wx.EVT_MENU, self.show_dialog, new_item)
        menubar.Append(record_menu, u'记录')
        self.SetMenuBar(menubar)

        self.init_grid()

    # 显示弹窗
    def show_dialog(self, event):
        Dialog(self, u'添加').ShowModal()

    # 绘制表格
    def init_grid(self):
        panel = wx.Panel(self, -1)
        grid = wx.grid.Grid(panel)
        data = GridData()
        grid.SetTable(data)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL)
        panel.SetSizer(sizer)


# 弹窗
class Dialog(wx.Dialog):
    def __init__(self, parent, title):
        super(Dialog, self).__init__(parent, title=title, size=(300, 250))
        self.Centre()
        panel = wx.Panel(self)

        wx.StaticText(panel, -1, label=u'名称：', pos=(20, 20), size=(-1, -1))
        self.name = wx.TextCtrl(panel, -1, value='', pos=(60, 20), size=(200, 20))
        wx.StaticText(panel, -1, label=u'帐号：', pos=(20, 50), size=(-1, -1))
        self.account = wx.TextCtrl(panel, -1, value='', pos=(60, 50), size=(200, 20))
        wx.StaticText(panel, -1, label=u'密码：', pos=(20, 80), size=(-1, -1))
        self.password = wx.TextCtrl(panel, -1, value='', pos=(60, 80), size=(200, 20))
        wx.StaticText(panel, -1, label=u'备注：', pos=(20, 110), size=(-1, -1))
        self.remark = wx.TextCtrl(panel, -1, value='', pos=(60, 110), size=(200, 20))

        button = wx.Button(panel, -1, label=u'保存', pos=(30, 150), size=(50, 50))
        self.Bind(wx.EVT_BUTTON, self.on_enter, button)

    def on_enter(self, event):
        name = self.name.GetValue()
        account = self.account.GetValue()
        password = self.password.GetValue()
        remark = self.remark.GetValue()

        if len(name) < 1 or len(account) < 1 or len(password) < 1 or len(remark) < 1:
            return False

        DataBase().insert(name, account, password, remark)
        self.Destroy()


# 加密解密
class Crypt:
    def __init__(self):
        self.key = '1234567890abcdef'
        self.mode = AES.MODE_CBC
        self.cipherText = ''

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    def encrypt(self, text):
        crypt = AES.new(self.key, self.mode, b'0000000000000000')
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 16
        count = len(text)

        if count < length:
            add = (length-count)
            # \0 backspace
            text += '\0' * add
        elif count > length:
            add = (length-(count % length))
            text += '\0' * add

        self.cipherText = crypt.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.cipherText)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        crypt = AES.new(self.key, self.mode, b'0000000000000000')
        plain_text = crypt.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')


# 数据库
class DataBase:

    def __init__(self):
        self.conn = sqlite3.connect('pass_admin.db')
        self.cursor = self.conn.cursor()

    # 查询数据
    def select(self):
        self.cursor.execute("\
            CREATE TABLE IF NOT EXISTS `password` (\
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,\
                `name` varchar(50) NOT NULL ,\
                `account` varchar(50) NOT NULL ,\
                `password` varchar(100) NOT NULL ,\
                `remark` varchar(200) \
            ) ;\
        ")
        self.cursor.execute("SELECT * FROM `password`")
        values = self.cursor.fetchall()

        crypt = Crypt()
        for i in xrange(len(values)):
            values[i] = list(values[i])
            values[i][1] = (crypt.decrypt(values[i][1])).decode('utf-8')
            values[i][2] = crypt.decrypt(values[i][2]).decode('utf-8')
            values[i][3] = crypt.decrypt(values[i][3]).decode('utf-8')
            values[i][4] = crypt.decrypt(values[i][4]).decode('utf-8')

        self.close()
        return values

    # 写入数据
    def insert(self, name, account, password, remark):
        crypt = Crypt()
        name = crypt.encrypt(name.encode('utf-8'))
        account = crypt.encrypt(account.encode('utf-8'))
        password = crypt.encrypt(password.encode('utf-8'))
        remark = crypt.encrypt(remark.encode('utf-8'))

        sql = "INSERT INTO `password` (`name`, `account`, `password`, `remark`) VALUES \
              ('"+name+"', '"+account+"', '"+password+"', '"+remark+"');"

        self.cursor.execute(sql)

        self.conn.commit()
        self.close()

    def close(self):
        self.cursor.close()
        self.conn.close()


# 表格
class GridData(wx.grid.PyGridTableBase):
    _cols = u"ID 名称 帐号 密码 备注".split()
    _data = DataBase().select()
    _highlighted = set()

    def GetColLabelValue(self, col):
        return self._cols[col]

    def GetNumberRows(self):
        return len(self._data)

    def GetNumberCols(self):
        return len(self._cols)

    def GetValue(self, row, col):
        return self._data[row][col]

    def SetValue(self, row, col, val):
        self._data[row][col] = val

    def GetAttr(self, row, col, kind):
        attr = wx.grid.GridCellAttr()
        attr.SetBackgroundColour(wx.GREEN if row in self._highlighted else wx.WHITE)
        return attr


# 主函数
def main():
    reload(sys)
    sys.setdefaultencoding('utf-8')

    app = wx.App(False)
    frame = MyFrame()
    frame.Centre()
    frame.Show(True)
    app.MainLoop()


if __name__ == '__main__':
    main()
