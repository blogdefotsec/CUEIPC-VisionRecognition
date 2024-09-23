##Emulator程序，请勿用于正式
import sensor, image time, math, pyb
form pybn import UART

#颜色阈值
blue = (16, 43, 17, 64, -101, -54)
red = (26, 43, 35, 82, -26, 57)
green =(21, 36, -48, -6, -32, 37)

#其他阈值
pixels_threshold = 100 #像素阈值
area_threshold = 100 #面积阈值
MoveThreshold = 10 #移动阈值，用于判断是否移动时的插值
color_thresholds = [[red],[green],[blue]] #0-红色，1-绿色，2-蓝色

#公共变量
#-传输到的2组颜色代码
ColorCode1=[0,0,0]
ColorCode2=[0,0,0]
#-当前帧Blobs状态
BlobState = [0,0,0] #注意此变量，全局变量将会在每一次获取Blobs时更新。详情见GetBlobState()
#-颜色组位置
ColorPosition=[0,0,0] #内容为0-红色，1-绿色，2-蓝色，顺序为由左向右的0-1-2
#-当前轮数
Round = 0

# 初始化串口
uart = UART(3, 115200)

#相机初始化程序
def CameraStartup():
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time = 200)
    sensor.set_auto_gain(False)
    sensor.set_auto_whitebal(False)
    sensor.set_auto_exposure(True)

#接受传输数据
def GetCode():
    global ColorCode1,ColorCode2
    temp = uart.read(2)
    DataRecieved = uart.read(6)
    DataRecieved = str(DataRecieved)
    ColorCode1 = [int(DataRecieved[2+i]) for i in range(3)]
    ColorCode2 = [int(DataRecieved[5+i]) for i in range(3)]

#获取当前帧Blobs状态
def GetBlobState():
    global BlobState,color_thresholds,pixels_threshold,area_threshold
    BlobState = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobState[i] = img.find_blobs(color_thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        #此处返回的BlobState[i]是一个列表，列表中每个元素都是一个二维列表，每个二维列表都是一个Blob对象。
        #其中，0号元素是红色的Blob对象，1号元素是绿色的Blob对象，2号元素是蓝色的Blob对象。
        #Blob对象中，0号元素是Blob的中心点，1号元素是Blob的面积，2号元素是Blob的颜色，3号元素是Blob的旋转角度，4号元素是Blob的旋转中心点，5号元素是Blob的旋转中心点的颜色。
        #举例：红色对象为BlobState[0]。Blob对象的操作参考：https://book.openmv.cc/image/blob.html

#圆盘位置检测程序
def CheckDiskPosition():
    #更新当前帧Blobs状态。
    GetBlobState()
    #循环到只出现一个颜色的Blob对象。
    while True:
        BlobCount = 0 #计数Blob对象个数
        for i in range(3):
            if BlobState[i] != 0:#非初始值
                BlobCount += 1 #检测到一个颜色
        #唯有出现一个颜色时
        if BlobCount == 1:
            break
        else:
            GetBlobState()#检测到多个颜色，重新获取Blobs状态。
    #退出循环时，只有一个颜色的Blob对象。
    #此时需要检测是否出现两个颜色的Blob对象。两个以上(考虑到运动产生杂色)的颜色出现，代表此时圆盘正在转动。
    while True:
        BlobCount = 0 #计数Blob对象个数
        for i in range(3):
            if BlobState[i]!= 0:#非初始值
                BlobCount += 1 #检测到一个颜色
        #出现两个颜色时
        if BlobCount >= 2:
            break
        else:
            GetBlobState() #检测到多个颜色，重新获取Blobs状态。
    #此处循环到重新只出现一个颜色，证明圆盘转动完毕。此时保证位置固定，允许机械臂进行夹取。
    while True:
        BlobCount = 0 #计数Blob对象个数
        for i in range(3):
            if BlobState[i]!= 0:#非初始值
                BlobCount += 1 #检测到一个颜色
        #出现一个颜色时
        if BlobCount == 1:
            break
        else:
            GetBlobState() #检测到多个颜色，重新获取Blobs状态。

#圆盘夹取程序
def GetDisk():
    global ColorCode1,ColorCode2,Round
    #确定当前轮数的颜色参考组。
    ColorReference=[0,0,0]
    if Round == 0:
        ColorReference = ColorCode1
    else:
        ColorReference = ColorCode2
    DiskGotCount = 0 #计数，当前取到了几个物料
    while DiskGotCount < 3:
        #获取当前帧Blobs状态。
        GetBlobState()
        #确认当前位置的颜色。
        for i in range(3):
            if BlobState[i] != 0:
                CurrentColor = i
        #查看当前轮数。轮数1则令颜色参考组为1，否则为2.
        #根据颜色指挥下位机夹取对应物料。
        if CurrentColor == ColorReference[DiskGotCount]:
            if CurrentColor == 0: #0-红色
                uart.write(str('R'))
                DiskGotCount += 1
            elif CurrentColor == 1: #1-绿色
                uart.write(str('G'))
                DiskGotCount += 1
            elif CurrentColor == 2: #2-蓝色
                uart.write(str('B'))
                DiskGotCount += 1
        #通过固定延时等待圆盘转到下一个物料。
        time.sleep(5.5)

#新版圆盘夹取程序
def GetDiskNew():
    global ColorPosition,Round,ColorCode1,ColorCode2
    #获取当前帧Blobs状态。
    GetBlobState()
    #更新位置表
    GetColorPosition()
    #确定当前轮数的颜色参考组。
    ColorReference=[0,0,0]
    if Round == 0:
        ColorReference = ColorCode1
    else:
        ColorReference = ColorCode2
    #按照ColorReference的顺序夹取对应物料
    for i in range(3):
        for j in range(3):
            if ColorReference[i] == ColorPosition[j]:#看看目前要夹得颜色的位置在哪里
                uart.write(str(j)) #意思是，目前要夹得颜色（也就是ColorReference[i]）在第j个位置(内容和ColorPosition[j]相同)，那么就夹取第j个物料

#圆盘识别程序
def CVDisk():
    #第一步：确定圆盘是否停稳了。
    CheckDiskPosition()
    #第二步：根据接收到的数据指挥下位机按顺序夹取对应物料
    GetDisk()

#新版圆盘识别程序
def CVDiskNew():
    #第一步：直到画面停止
    while CheckMotionStatic() == False:
        pass
    #第二步：根据位置表指挥下位机按顺序夹取对应物料
    GetDiskNew()

#检测当前画面是否静止
def CheckMotionStatic():
    #公有变量，表示两帧差距阈值，超出该值视为运动
    global MoveThreshold, BlobState
    #私有变量，储存用于对比的第一帧Blobs状态
    BlobState1 = [0,0,0]
    #以及第二帧
    BlobState2 = [0,0,0]
    #更新当前帧Blobs状态。
    GetBlobState()
    #此处更新BlobState1
    for i in range(3):
        if BlobState[i]!= 0:
            BlobState1[i] = BlobState[i]
    #再次获取当前帧Blobs状态。
    GetBlobState()
    #此处更新BlobState2
    for i in range(3):
        if BlobState[i]!= 0:
            BlobState2[i] = BlobState[i]
    #若两帧Blobs状态（红色x轴坐标值、绿色x轴坐标值、蓝色x轴坐标值）差距小于阈值，则认为静止。
    stillflag = False
    for i in range(3):
        if abs(BlobState1[i].cx() - BlobState2[i].cx()) < MoveThreshold:
            stillflag = True
    return stillflag

#将识别颜色与位置表相连
def GetColorPosition():
    #请先确保ColorCode1和ColorCode2已被赋值，且获取过Blobs状态。
    global ColorPosition,BlobState
    ColorPosition = [0,0,0]
    cx=[0,0,0]#三种颜色的x轴坐标。当然是0-红色，1-绿色，2-蓝色。
    #从Blobs状态中获取三色块的x轴坐标。
    for i in range(3):
        cx[i] = BlobState[i].cx()
    #对比三种颜色块的x轴坐标，判断左边（最小的）、中间、右边（最大值）分别是哪个颜色
    for i in range(3):
        if cx[i] < cx[0]:
            ColorPosition[i] = 0
        elif cx[i] > cx[0] and cx[i] < cx[1]:
            ColorPosition[i] = 1
        else:
            ColorPosition[i] = 2

#自由打靶程序
def CVShooting():
    global ColorPosition,ColorCode1,ColorCode2,BlobState,Round
    #获取当前帧Blobs状态。
    GetBlobState()
    #获取颜色位置
    GetColorPosition()
    #将颜色位置进行汇报
    

#Emulator主程序
while True:
    if (uart.any()):
        #选择运行模式
        ModeSelect = uart.read()
        if ModeSelect == b'c':#模式选择：c-扫码传输颜色组
            GetCode()
        elif ModeSelect == b's': #模式选择：s-旧版圆盘识别
            Round=1
            CameraStartup()
            CVDisk() #圆盘识别程序
            uart.write(str('j')) #在下位机中定义的阶段停止标志
        elif ModeSelect == b'b': #模式选择：b-第二次旧版圆盘识别，程序相同
            Round=2
            CameraStartup()
            CVDisk()
            uart.write(str('s'))
        elif ModeSelect == b'r': #模式选择：r-新版圆盘识别
            Round=1
            CameraStartup()
            CVDiskNew()
            uart.write(str('j'))
        elif ModeSelect == b'f': #模式选择：f-第二次新版圆盘识别，程序相同
            Round=2
            CameraStartup()
            CVDiskNew()
            uart.write(str('s'))
        elif ModeSelect == b'd': #模式选择：d-自由打靶(决赛)
            CameraStartup()
            CVShooting()
            uart.write(str('d'))