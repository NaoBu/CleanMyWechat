from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsDropShadowEffect, QListWidgetItem, QListView, QWidget, QLabel, QHBoxLayout, QFileDialog
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QMutex, QSize, QEvent, QPoint
from PyQt5.QtGui import QMouseEvent, QCursor, QColor
from PyQt5.uic import loadUi

from pathlib import Path, PureWindowsPath
from dateutil import relativedelta
import os, datetime, time, re, math, resources, shutil, json

from deleteThread import *
from selectVersion import *

working_dir = os.path.split(os.path.realpath(__file__))[0]

# 主窗口
class Window(QMainWindow):

    def mousePressEvent(self, event):
        # 重写一堆方法使其支持拖动
        if event.button()==Qt.LeftButton:
            self.m_drag=True
            self.m_DragPosition=event.globalPos()-self.pos()
            event.accept()
            #self.setCursor(QCursor(Qt.OpenHandCursor))
    def mouseMoveEvent(self, QMouseEvent):
        try:
            if Qt.LeftButton and self.m_drag:
                self.move(QMouseEvent.globalPos()-self.m_DragPosition)
                QMouseEvent.accept()
        except:
            pass
    def mouseReleaseEvent(self, QMouseEvent):
        self.m_drag=False
        #self.setCursor(QCursor(Qt.ArrowCursor))

    def _frame(self):
        # 边框
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 阴影
        effect = QGraphicsDropShadowEffect(blurRadius=12, xOffset=0, yOffset=0)
        effect.setColor(QColor(25, 25, 25, 170))
        self.mainFrame.setGraphicsEffect(effect)
    def doFadeIn(self):
        # 动画
        self.animation = QPropertyAnimation(self, b'windowOpacity')
        # 持续时间250ms
        self.animation.setDuration(250)
        try:
        # 尝试先取消动画完成后关闭窗口的信号
            self.animation.finished.disconnect(self.close)
        except:
            pass
        self.animation.stop()
        # 透明度范围从0逐渐增加到1
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()
    def doFadeOut(self):
        self.animation.stop()
        # 动画完成则关闭窗口
        self.animation.finished.connect(self.close)
        # 透明度范围从1逐渐减少到0s
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()
    def setWarninginfo(self, text):
        self.lab_info.setStyleSheet(
                    """
                    .QLabel {
	                    border:1px solid #ffccc7;
	                    border-radius:3px;
	                    line-height: 140px;
	                    padding: 5px;
	                    color: #434343;
	                    background: #fff2f0;
                    }
                    """
                )
        self.lab_info.setText(text)
    def setSuccessinfo(self, text):
        self.lab_info.setStyleSheet(
                    """
                    .QLabel {
	                    border:1px solid #b7eb8f;
	                    border-radius:3px;
	                    line-height: 140px;
	                    padding: 5px;
	                    color: #434343;
	                    background: #f6ffed;
                    }
                    """
                )
        self.lab_info.setText(text)

class ConfigWindow(Window):
    def _connect(self):
        self.combo_user.currentIndexChanged.connect(self.refresh_ui)
        #self.line_wechat.textChanged.connect(self.create_config)
        self.btn_close.clicked.connect(self.doFadeOut)
        self.btn_file.clicked.connect(self.open_file)

        self.check_is_clean.stateChanged.connect(self.update_config)
        self.check_picdown.stateChanged.connect(self.update_config)
        self.check_files.stateChanged.connect(self.update_config)
        self.check_video.stateChanged.connect(self.update_config)
        self.check_picscache.stateChanged.connect(self.update_config)
        self.line_gobackdays.textChanged.connect(self.update_config)

    def open_file(self):
        self.openfile_name = QFileDialog.getExistingDirectory(self,'选择微信数据目录','')

    def check_wechat_exists(self):
        self.selectVersion = selectVersion()
        self.version_scan = self.selectVersion.getAllPath()[0]
        self.users_scan = self.selectVersion.getAllPath()[1]
        if len(self.version_scan) == 0:
            return False
        else:
            return True
    def load_config(self):
        self.config = open(working_dir+"/config.json", encoding="utf-8")
        self.config = json.load(self.config)

        for value in self.config["users"]:
            self.combo_user.addItem(value["wechat_id"])

        self.line_gobackdays.setText(str(self.config["users"][0]["clean_days"]))
        self.check_is_clean.setChecked(self.config["users"][0]["is_clean"])
        self.check_picdown.setChecked(self.config["users"][0]["clean_pic"])
        self.check_files.setChecked(self.config["users"][0]["clean_file"]) 
        self.check_video.setChecked(self.config["users"][0]["clean_video"])
        self.check_picscache.setChecked(self.config["users"][0]["clean_pic_cache"])
        self.setSuccessinfo("加载配置文件成功")
    def refresh_ui(self):
        self.config = open(working_dir+"/config.json", encoding="utf-8")
        self.config = json.load(self.config)

        for value in self.config["users"]:
            if value["wechat_id"] == self.combo_user.currentText():
                self.line_gobackdays.setText(str(value["clean_days"]))
                self.check_is_clean.setChecked(value["is_clean"])
                self.check_picdown.setChecked(value["clean_pic"])
                self.check_files.setChecked(value["clean_file"]) 
                self.check_video.setChecked(value["clean_video"])
                self.check_picscache.setChecked(value["clean_pic_cache"])
    def create_config(self):
        true = True
        false = False
        if not os.path.exists(working_dir+"/config.json"): 
            if not self.check_wechat_exists():
                if os.path.exists(self.openfile_name):
                    dirlist = []
                    list_ = os.listdir(self.openfile_name)
                    list_.remove('All Users')
                    list_.remove('Applet')
                    for i in range(0, len(list_)):
                        file_path = os.path.join(self.openfile_name, list_[i])
                        if os.path.isdir(file_path):
                            dirlist.append(file_path)
                    self.version_scan = dirlist
                    self.users_scan = list_
                    self.setSuccessinfo("扫描目录成功")
                else:
                    if self.openfile_name == "":
                        self.setWarninginfo("默认位置没有微信，请自定义位置")
                    else:
                        self.setWarninginfo("目录非微信数据目录，请检查")
                    return

            self.config = {
                "data_dir" : self.version_scan,
                "users" : []
            }
            for value in self.users_scan:
                self.config["users"].append({
                    "wechat_id" : value,
                    "clean_days": 365,
                    "is_clean": true,
                    "clean_pic_cache": true,
                    "clean_file": true,
                    "clean_pic": true,
                    "clean_video": true,
                    "is_timer": true,
                    "timer": "0h"
                })
            with open(working_dir+"/config.json","w",encoding="utf-8") as f:
                json.dump(self.config,f)
            self.setSuccessinfo("加载配置文件成功")
            self.load_config()
        else:
            self.setSuccessinfo("加载配置文件成功")
            self.load_config()
    def update_config(self):
        true = True
        false = False

        self.config = open(working_dir+"/config.json", encoding="utf-8")
        self.config = json.load(self.config)

        for value in self.config["users"]:
            if value["wechat_id"] == self.combo_user.currentText():
                value["clean_days"] = self.line_gobackdays.text()
                value["is_clean"] = self.check_is_clean.isChecked()
                value["clean_pic"] = self.check_picdown.isChecked() 
                value["clean_file"] = self.check_files.isChecked() 
                value["clean_video"] = self.check_video.isChecked() 
                value["clean_pic_cache"] = self.check_picscache.isChecked() 
        
        with open(working_dir+"/config.json","w",encoding="utf-8") as f:
            json.dump(self.config,f)
        self.setSuccessinfo("更新配置文件成功")

    def __init__(self):
        super().__init__()
        loadUi(working_dir+"/ui/config.ui", self)

        self._frame()
        self._connect()

        self.doFadeIn()
        self.create_config()

        self.show()

class MainWindow(Window):

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonPress:
            if object == self.lab_close:
                self.doFadeOut()
                return True
            elif object == self.lab_clean:
                try:
                    self.setSuccessinfo("正在清理中...")
                    self.justdoit()
                except:
                    self.setWarninginfo("清理失败，请检查配置文件后重试")
                return True
            elif object == self.lab_config:
                win = ConfigWindow()
                return True
        return False
    def _eventfilter(self):
        # 事件过滤
        self.lab_close.installEventFilter(self)
        self.lab_clean.installEventFilter(self)
        self.lab_config.installEventFilter(self)

    def get_fileNum(self, path, day, picCacheCheck, fileCheck, picCheck,
                   videoCheck):
        dir_name = PureWindowsPath(path)
        # Convert path to the right format for the current operating system
        correct_path = Path(dir_name)
        now = datetime.datetime.now()
        if picCacheCheck:
            path_one = correct_path / 'Attachment'
            path_two = correct_path / 'FileStorage/Cache'
            self.getPathFileNum(now, day, path_one, path_two)
        if fileCheck:
            path_one = correct_path / 'Files'
            path_two = correct_path / 'FileStorage/File'
            self.getPathFileNum(now, day, path_one, path_two)
        if picCheck:
            path_one = correct_path / 'Image/Image'
            path_two = correct_path / 'FileStorage/Image'
            self.getPathFileNum(now, day, path_one, path_two)
        if videoCheck:
            path_one = correct_path / 'Video'
            path_two = correct_path / 'FileStorage/Video'
            self.getPathFileNum(now, day, path_one, path_two)
    def pathFileDeal(self, now, day, path):
        if os.path.exists(path):
            list = os.listdir(path)
            filelist = []
            for i in range(0, len(list)):
                file_path = os.path.join(path, list[i])
                if os.path.isfile(file_path):
                    filelist.append(list[i])
            for i in range(0, len(filelist)):
                file_path = os.path.join(path, filelist[i])
                if os.path.isdir(file_path):
                    continue
                timestamp = datetime.datetime.fromtimestamp(
                    os.path.getmtime(file_path))
                #r = relativedelta.relativedelta(now, timestamp)
                #if r.years * 12 + r.months > month:
                diff = (now - timestamp).days
                if diff > day:
                    self.file_list.append(file_path)
    def getPathFileNum(self, now, day, path_one, path_two):
        # caculate path_one
        self.pathFileDeal(now, day, path_one)

        # caculate path_two
        if os.path.exists(path_two):
            osdir = os.listdir(path_two)
            dirlist = []
            month = math.ceil(day / 29)
            for i in range(0, len(osdir)):
                file_path = os.path.join(path_two, osdir[i])
                if os.path.isdir(file_path):
                    dirlist.append(osdir[i])
            for i in range(0, len(dirlist)):
                file_path = os.path.join(path_two, dirlist[i])
                if os.path.isfile(file_path):
                    continue
                if re.match('\d{4}(\-)\d{2}', dirlist[i]) != None:
                    cyear = int(dirlist[i].split('-', 1)[0])
                    cmonth = int(dirlist[i].split('-', 1)[1])
                    diff = (now.year - cyear) * 12 + now.month - cmonth
                    if diff > month:
                        self.dir_list.append(file_path)
                    elif diff == month:
                        self.pathFileDeal(now, day, file_path)
                        #print("delete:", file_path)

    def callin(self):
        #另起一个线程来实现删除文件和更新进度条
        self.calc = deleteThread(self.file_list, self.dir_list)
        self.calc.delete_proess_signal.connect(self.callback)
        self.calc.start()
        #self.calc.exec()
    def callback(self, value):
        self.bar_progress.setValue(value)
        if value == 100:
            out = "本次共清理文件" + str(len(self.file_list)) + "个，文件夹" + str(
                len(self.dir_list)) + "个。请前往回收站检查并清空。"
            self.setSuccessinfo(out)
            return
    def justdoit(self): # 这个Api设计的太脑残了，其实dir可以直接放在user里的... 有时间改吧
        self.file_list = []
        self.dir_list = []
        self.config = open(working_dir+"/config.json", encoding="utf-8")
        self.config = json.load(self.config)
        i = 0
        for value in self.config["users"]:
            if value["is_clean"]:
                self.get_fileNum(self.config["data_dir"][i], int(value["clean_days"]), value["clean_pic_cache"],value["clean_file"], value["clean_pic"], value["clean_video"])
            i = i + 1
                
            if len(self.file_list) + len(self.dir_list) == 0:
                self.setWarninginfo("没有需要清理的文件（可能是您没打勾哦）")
                
            self.callin()

    def __init__(self):
        super().__init__()
        loadUi(working_dir+"/ui/main.ui", self)

        self._frame()
        self._eventfilter()
        self.doFadeIn()

        # 判断配置文件是否存在
        if not os.path.exists(working_dir+"/config.json"):
            self.setWarninginfo("配置文件不存在！请单击“设置”创建配置文件")

        self.show()


if __name__ == '__main__':
    app = QApplication([])
    win = MainWindow()
    app.exec_()