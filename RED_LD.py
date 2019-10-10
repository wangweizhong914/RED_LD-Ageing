#author：wwz
#data: 2019/2/27
#Version: V1.0
#Project: Red LD
#V1.0 First


# -*- encoding=UTF-8 -*-
__version__ = 'V1.0'

from ThorlabsPM100 import ThorlabsPM100
import serial
import serial.tools.list_ports
import os
import time
import datetime
import threading
from tkinter import ttk
from tkinter import *
from tkinter import  messagebox
from tkinter import  filedialog
import tkinter.messagebox #这个是消息框，对话框的关键
import visa
import sqlite3
import MyThread

#设置Label的内容
def SetInfo(type,text):
    tkinter.messagebox.showinfo(type, text)

#获取PM100USB驱动接口
def GetPM100NOList():
    rm = visa.ResourceManager()
    PM100_list = rm.list_resources()
    return PM100_list

#更新PM100USB驱动接口
def PM100SelectComboboxUpdate(event = None):
    selectCombobox['values'] = GetPM100NOList()


#获取激光驱动接口
def GetLaserNoList():
    port_serial = []
    port_list = list(serial.tools.list_ports.comports())
    for i in list(port_list):
        port_serial.append(i[0])
    return port_serial

#更新激光驱动接口
def LaserSelectComboboxUpdate(event = None):
    LDselectCombobox['values'] = GetLaserNoList()

'''
def Serial_Data_Check(ser,data):#串口读取校验
    data_read = []
    while ser.inWaiting() > 0:
        data_read.append[ser.read(1)]
    for i in data_read:
        if i not in data:
            return  False
    return True
'''
#功率采集
def Power_Get():
    global ser_laser, ser_motor, power_meter

    stepforword = bytes([0XBA,0X07,0XF8,0X0C,0X00,0X03,0X01,0X30,0X00,0X63,0X9C,0X00,0XC8,0X00,0XC8,0X84,0XFE ])#电机运行至激光输出位置
    stepback    = bytes([0XBA,0X07,0XF8,0X0C,0X00,0X03,0X02,0X30,0X00,0X63,0X9C,0X00,0XC8,0X00,0XC8,0X87,0XFE])#电机归零
    stepstop    = bytes([0XBA,0X07,0XF8,0X0C,0X00,0X03,0X03,0X30,0X00,0X63,0X9C,0X00,0XC8,0X00,0XC8,0X86,0XFE])#电机停止

    TestPos1_On   = bytes([0xFF,0X02,0X01,0X01,0X01,0XDD, 0xFF,0X02,0X01,0X02,0X01,0XDD,0xFF,0X02,0X01,0X03,0X01,0XDD])#测试工位1激光输出
    TestPos1_Off  = bytes([0xFF,0X02,0X01,0X01,0X00,0XDD, 0xFF,0X02,0X01,0X02,0X00,0XDD,0xFF,0X02,0X01,0X03,0X00,0XDD])#测试工位1激光关闭
    TestPos2_On   = bytes([0xFF,0X02,0X01,0X04,0X01,0XDD, 0xFF,0X02,0X01,0X05,0X01,0XDD,0xFF,0X02,0X01,0X06,0X01,0XDD])#测试工位2激光输出
    TestPos2_Off  = bytes([0xFF,0X02,0X01,0X04,0X00,0XDD, 0xFF,0X02,0X01,0X05,0X00,0XDD,0xFF,0X02,0X01,0X06,0X00,0XDD])#测试工位2激光关闭
    TestPos3_On   = bytes([0xFF,0X02,0X01,0X07,0X01,0XDD, 0xFF,0X02,0X01,0X08,0X01,0XDD,0xFF,0X02,0X01,0X09,0X01,0XDD])
    TestPos3_Off  = bytes([0xFF,0X02,0X01,0X07,0X00,0XDD, 0xFF,0X02,0X01,0X08,0X00,0XDD,0xFF,0X02,0X01,0X09,0X00,0XDD])
    TestPos4_On   = bytes([0xFF,0X02,0X01,0X0A,0X01,0XDD, 0xFF,0X02,0X01,0X0B,0X01,0XDD,0xFF,0X02,0X01,0X0C,0X01,0XDD])
    TestPos4_Off  = bytes([0xFF,0X02,0X01,0X0A,0X00,0XDD, 0xFF,0X02,0X01,0X0B,0X00,0XDD,0xFF,0X02,0X01,0X0C,0X00,0XDD])

    gather_time = 30  # 测量时间间隔 min
    timeset = int(float(TimeSet.get()) * 60 / gather_time)  # 测量时间设定

    ser_motor.write(stepback)#回退至原点
    time.sleep(15)
    ser_motor.write(stepstop)  # 停止
    time.sleep(5)
    ser_laser.write(TestPos1_On)
    ser_laser.write(TestPos3_On)
    #ser_laser.write(TestPos4_On)
    # ser_motor.write(stepback)  # 回退至原点
    # time.sleep(15)
    # ser_motor.write(stepforword)  # 前进至激光处
    # time.sleep(15)
    # ser_motor.write(stepstop)  # 停止
    # time.sleep(5)

    while 1:
        if GetPowerButton['text'] == "停止":
            ser_laser.write(TestPos1_On)
            ser_laser.write(TestPos3_On)
            #ser_laser.write(TestPos4_On)
            time.sleep(1800)#每30分钟采集一次功率值
            ser_motor.write(stepforword)  # 前进至激光处
            time.sleep(10)
            ser_laser.write(TestPos3_Off)
            time.sleep(1)
            print('测试工位1功率值：'+power_meter.read)  # Read-only property
            ser_laser.write(TestPos3_On)
            ser_laser.write(TestPos1_Off)
            time.sleep(1)
            print('测试工位3功率值：'+power_meter.read)
            ser_motor.write(stepback)
        elif GetPowerButton['text']=='错误'or GetPowerButton['text']=='执行':
            power_meter.abort() #测量中止
            return
        else:
            power_meter.abort()
            return
    return

#运行时间计算
def Time_Calc(timeset):
    time_total = int(float(timeset) * 3600)  # 测量时间设定
    for i in range(time_total):
        if GetPowerButton['text'] == "停止":
            TimeSpend.set(str(datetime.timedelta(seconds=i)))
            time.sleep(1)
        elif GetPowerButton['text'] == "错误" or GetPowerButton['text'] == "执行":
            return  #程序执行完毕
    return


def Sys_Init():
    global ser_laser, ser_motor,power_meter
    count = 10  # 默认采样取10次平均
    if not PM100NO.get() in GetPM100NOList():
        SetInfo('提示', '请连接激光功率计')
        return False
    else:# 功率计配置
        try:
            rm = visa.ResourceManager()
            inst = rm.open_resource(PM100NO.get())
        except:
            SetInfo('错误', '连接功率计失败')
            return False
        #参数配置
        power_meter = ThorlabsPM100(inst=inst)
        power_meter.sense.average.count = count  # write property
        power_meter.system.beeper.immediate()  # method
        print(power_meter.read)  # Read-only property
        print(power_meter.sense.average.count)  # read property
    if not StepMotor.get() in GetLaserNoList():
        SetInfo('提示','请连接丝杆滑台')
        return False
    else:# 丝杆滑杆配置
        try:
            ser_motor = serial.Serial(StepMotor.get(), 9600, timeout=0.5)
        except:
            SetInfo('错误','连接丝杆滑台失败')
            return  False
    if not LaserNo.get() in GetLaserNoList():
        SetInfo('提示','请连接激光驱动器')
        return False
    else: # 激光驱动板配置
        try:
            ser_laser = serial.Serial(LaserNo.get(), 9600, timeout=0.5)
        except:
            SetInfo('错误','连接激光驱动板失败')
        # 激光器全局开
        ser_laser.write([0xff])
        ser_laser.write([0x06])
        ser_laser.write([0x01])
        ser_laser.write([0xdd])
    return True


def GetPower():
    global ser_laser, ser_motor, power_meter
    if GetPowerButton['text'] == "开始":

        if Sys_Init() is False: #系统初始化
            GetPowerButton['text'] = "错误"
            return
        else:
            GetPowerButton['text'] = "执行"
    elif  GetPowerButton['text'] == "执行":
        GetPowerButton['text'] = "停止"
        # 创建功率采集线程
        GetPowerThread = MyThread.MyThread(func=Power_Get, args=())
        GetPowerThread.setDaemon(True)
        GetPowerThread.start()
        # 创建计时线程
        TimeCalcThread = MyThread.MyThread(func=Time_Calc, args=(TimeSet.get()))
        TimeCalcThread.setDaemon(True)
        TimeCalcThread.start()
    else:
        #激光器全局关
        ser_laser.write([0xff])
        ser_laser.write([0x06])
        ser_laser.write([0x00])
        ser_laser.write([0xdd])
        ser_laser.close()#关闭激光驱动板控制接口
        ser_motor.close()#关闭丝杠滑杆接口
        GetPowerButton['text'] = "开始"
    return






if __name__ == '__main__':
    #以下是界面相关代码
    root = Tk(className = '红光LD')
    root.resizable(width=False,height=False)
    root.geometry('620x270')
    menubar = Menu(root)
    filemenu= Menu(menubar, tearoff=0)

    root.config(menu = menubar)
    body = Frame(root)

    #设备接口连接
    lab1=Label(body,text='设备连接')
    lab1.grid(padx=4, pady=2, row=0, column=0, sticky='S' + 'N' + 'E' + 'W')
    lab1.configure(fg='blue')
    #PM100驱动接口获取
    Label(body,text='PM100USB').grid(padx=4,pady=2,row=0,column=1,sticky='S'+'N'+'E'+'W')
    PM100NO =StringVar()
    selectCombobox = ttk.Combobox(body,textvariable=PM100NO, width=10)
    selectCombobox['values']=GetPM100NOList()
    if selectCombobox['values']!=():
        PM100NO.set(selectCombobox['values'][0])
    selectCombobox.grid(row=0,column =2, sticky ='E'+'W')
    selectCombobox.bind('<Button-1>', PM100SelectComboboxUpdate)
    # 激光驱动接口获取
    Label(body, text='激 光 驱 动 板').grid(padx=4, pady=2, row=0, column=3, sticky='S' + 'N' + 'E' + 'W')
    LaserNo = StringVar()
    LDselectCombobox = ttk.Combobox(body, textvariable=LaserNo, width=10)
    LDselectCombobox['values'] = GetLaserNoList()
    if LDselectCombobox['values'] != ():
        LaserNo.set(LDselectCombobox['values'][0])
    LDselectCombobox.grid(row=0, column=4, sticky='E' + 'W')
    LDselectCombobox.bind('<Button-1>', LaserSelectComboboxUpdate)

    # 丝杠接口获取
    Label(body, text='丝杠滑台').grid(padx=4, pady=2, row=0, column=5, sticky='S' + 'N' + 'E' + 'W')
    StepMotor = StringVar()
    SMselectCombobox = ttk.Combobox(body, textvariable=StepMotor, width=10)
    SMselectCombobox['values'] = GetLaserNoList()
    if SMselectCombobox['values'] != ():
        StepMotor.set(SMselectCombobox['values'][0])
    SMselectCombobox.grid(row=0, column=6, sticky='E' + 'W')
    SMselectCombobox.bind('<Button-1>', LaserSelectComboboxUpdate)

    #参数设置
    lab1=Label(body,text='参数设置')
    lab1.grid(padx=4, pady=2, row=1, column=0, sticky='S' + 'N' + 'E' + 'W')
    lab1.configure(fg='blue')
    # 输出电流
    CurValue = StringVar(value='6')
    Label(body, text='电    流(A)').grid(padx=4, pady=2, row=1, column=1, sticky='S' + 'N' + 'E' + 'W')
    Entry(body, textvariable=CurValue, width=8).grid(padx=4, pady=2, row=1, column=2, sticky='S' + 'N' + 'E' + 'W')
    # 测试定时
    TimeSet = StringVar(value='1')
    Label(body, text='测试定时(小时)').grid(padx=4, pady=2, row=1, column=3, sticky='S' + 'N' + 'E' + 'W')
    Entry(body, textvariable=TimeSet, width=10).grid(padx=4, pady=2, row=1, column=4, sticky='S' + 'N' + 'E' + 'W')
    # 测试历时
    TimeSpend = StringVar(value='0:00:00')
    Label(body, text='测量历时').grid(padx=4, pady=2, row=1, column=5, sticky='S' + 'N' + 'E' + 'W')
    Entry(body, textvariable=TimeSpend, width=10).grid(padx=4, pady=2, row=1, column=6, sticky='S' + 'N' + 'E' + 'W')

    #分割线
    sh = ttk.Separator(body, orient=HORIZONTAL)
    sh.grid(pady=15, row=2, column=0, columnspan=10, sticky="we")

    #光功率采样执行
    GetPowerButton = Button(body, text='开始',font=("Arial", 20),width=8,height=2,bg='white',command=lambda :GetPower())
    GetPowerButton.grid(padx=4,pady=2,row=3,column=2,rowspan=3,columnspan =3)
    body.grid(padx=10,pady=2)

    # 分割线
    sh = ttk.Separator(body, orient=HORIZONTAL)
    sh.grid(pady=15, row=6, column=0, columnspan=10, sticky="we")

    sh = ttk.Separator(body, orient=HORIZONTAL)
    sh.grid(pady=15, row=7, column=0, columnspan=10, sticky="we")
    root.mainloop()




























