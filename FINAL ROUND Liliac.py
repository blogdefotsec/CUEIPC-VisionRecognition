############################################
#               固件说明                   #
############################################
#               固件版本：Fighting         #
#               版本号：0.9                #
###########################################
#               固件说明：                 #
#  圆盘识别程序追加中                      #
###########################################
#            XYNOSURE 2023-12-03          #
###########################################

import sensor, image, time, math,pyb
from pyb import UART
from pyb import LED
from pyb import Pin

#灯带I/O
Lighting = Pin('P6',Pin.OUT_OD)
Lighting.high()## 灯带给高电平失电，低电平得电。出现问题时，查看继电器到底是绿灯闪烁（信号线不稳）还是红灯闪烁（线圈电源不稳）

#通用程序
BlobStateTemp=[0,0,0]
ColorPositionTemp=[0,0,0]

#颜色阈值
blue = (0, 59, 2, 56, -76, -20)#(0, 29, -40, 35, -97, -5)#(0, 47, -128, 31, -128, -13)
red = (12, 78, 15, 127, 6, 62)#(12, 78, 15, 127, 6, 62)#(9, 51, 23, 96, -10, 81)#(14, 40, 18, 52, 1, 127)
green = (12, 61, -78, -12, -40, 55)#(0, 51, -96, -14, -19, 54)
(11, 78, 15, 127, 27, 49)
#定位圆阈值
DetectThreshold = 2000 #圆阈值
RMIN = 44 #半径最小值
RMAX = 55 #半径最大值
Xstart = 130 #X轴起始位置
Xend = 150 #X轴结束位置

#其他阈值
pixels_threshold = 900 #像素阈值
area_threshold = 500 #面积阈值
MoveThreshold = 5 #移动阈值，用于判断是否移动时的插值
StopThreshold = 2 #停止阈值
color_thresholds = [[red],[green],[blue]] #0-红色，1-绿色，2-蓝色

#决赛
CVShootMode = 1 #1-识别前一个靶（顺时针），2-识别后一个靶（逆时针），3-
#-六色块
roiUp=[0,54,320,70]#平分画面上侧
roiDown=[0,141,320,70]#平分画面下侧
ColorPositionUp = [0,1,2]#上台阶颜色位置
ColorPositionDown = [1,2,0]#下台阶颜色位置
BlobStateUp = [0,0,0] #决赛 上位置检测
BlobStateDown = [0,0,0]#决赛 下位置检测
FTH01 = 94 #定位01位置X轴分界线
FTH12 = 200 #定位12位置X轴分界线
#-圆盘
roiFF=[114,101,68,71] #定位前一个靶的区域
roiBB=[114,101,68,71] #定位后一个靶的区域
#HD模式！
roiTarget=[218,77,155,61]#定位正位靶的位置
roiCircle=[198,0,167,151]#圆定位位置
BlobStateTarget = [0,0,0]
BlobStateFF = [0,0,0]
BlobStateBB = [0,0,0]
BlobStateEmpty = [0,0,0]
CircleState = 0
TargetBlue = (0, 59, 2, 56, -76, -20)#蓝色靶阈值
TargetRed = (56, 70, 6, 127, -2, 30)#红色靶阈值
TargetGreen = (66, 84, -29, -11, 10, 20)#绿色靶阈值
TargetThresholds = [[TargetRed],[TargetGreen],[TargetBlue]]#0-红色，1-绿色，2-蓝色
TargetPix = 5#靶像素阈值
TargetArea = 5#靶面积阈值
EmptyPix = 700#物料像素阈值
EmptyArea = 100#物料面积阈值
MissCount = 2#等待靶数，大于轮次丢弃
#-第二区域识别
AREA2COLOR = [0,0,0] #1-红色 2-绿色 3-蓝色
roiSAD1=[4,165,123,165]
roiSAD2=[161,157,192,188]
roiSAD3=[419,176,149,153]
SADpix = 10
SADarea = 10
#-Old
roiLow=[70,129,188,109]


#公共变量

#-传输到的2组颜色代码
ColorCode1=[0,1,2]
ColorCode2=[1,2,0]

#-当前帧Blobs状态
BlobState = [0,0,0] #注意此变量，全局变量将会在每一次获取Blobs时更新。详情见GetBlobState()
BlobStateLow = [0,0,0] #低位置检测，用于旧版程序

#-颜色组位置
ColorPosition=[0,0,0] #下标为0-红色，1-绿色，2-蓝色，内容对应为0号、1号、2号位置（画面的左、中、右三分之一）
XTH01 = 106 #定位01位置X轴分界线
XTH12 = 189 #定位12位置X轴分界线

#-当前轮数
Round = 0

# 初始化串口-非调试模式请改成3！！！！！！！！！！！！！！！！！！！！！！！！！！！
uart = UART(3, 115200)

#相机初始化程序
def CameraStartup():
    print("Camera Startup\n")
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_windowing((320, 240))
    sensor.skip_frames(time = 200)
    ##sensor.set_auto_gain(False)
    ##sensor.set_auto_whitebal(False)
    ##sensor.set_auto_exposure(False, 8000)#注意此处，通过调节参数2（曝光时间）来控制画面明度

#决赛-第二区域颜色识别程序
def FinalSecondAreaDetect():
    global roiSAD1,roiSAD2,roiSAD3,color_thresholds,SADpix,SADarea,AREA2COLOR
    print("Final Secound Area Detect\n")
    BlobStateSAD1 = [0,0,0]
    BlobStateSAD2 = [0,0,0]
    BlobStateSAD3 = [0,0,0]
    #接下来是识别部分，分别是别SAD1、SAD2、SAD3区域的颜色
    finishFlag = 0 #该变量用于判断是否识别到颜色。
    CameraStartupHDFree()
    while finishFlag != 1:
        finishFlag = 0
        img = sensor.snapshot().lens_corr(1.8)
        #获取颜色对象
        for i in range(3):
            BlobStateSAD1[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=SADpix, area_threshold=SADarea, merge=True, roi=roiSAD1)
            if BlobStateSAD1[i]:
                print("AREA1 Get Color",i)
                for b in BlobStateSAD1[i]:
                    if i==0:
                        img.draw_rectangle(b.rect(),color = (255,152,152))
                    elif i==1:
                        img.draw_rectangle(b.rect(),color = (152,255,152))
                    elif i==2:
                        img.draw_rectangle(b.rect(),color = (152,152,255))
                    img.draw_cross(b.cx(), b.cy())
                pass
            else:
                BlobStateSAD1[i] = 0
        #识别结束后，判断是否识别到颜色
        for i in range(3):
            if BlobStateSAD1[i] != 0:
                finishFlag = finishFlag+1
    finishFlag = 0
    while finishFlag != 1:
        finishFlag = 0
        img = sensor.snapshot().lens_corr(1.8)
        for i in range(3):
            BlobStateSAD2[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=SADpix, area_threshold=SADarea, merge=True, roi=roiSAD2)
            if BlobStateSAD2[i]:
                print("AREA2 Get Color",i)
                for b in BlobStateSAD2[i]:
                    if i==0:
                        img.draw_rectangle(b.rect(),color = (255,152,152))
                    elif i==1:
                        img.draw_rectangle(b.rect(),color = (152,255,152))
                    elif i==2:
                        img.draw_rectangle(b.rect(),color = (152,152,255))
                    img.draw_cross(b.cx(), b.cy())
                pass
            else:
                BlobStateSAD2[i] = 0
            #print(BlobStateSAD2)
        for i in range(3):
            if BlobStateSAD2[i] != 0:
                finishFlag = finishFlag+1
    finishFlag = 0
    while finishFlag != 1:
        img = sensor.snapshot().lens_corr(1.8)
        for i in range(3):
            BlobStateSAD3[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=SADpix, area_threshold=SADarea, merge=True, roi=roiSAD3)
            if BlobStateSAD3[i]:
                print("AREA3 Get Color",i)
                for b in BlobStateSAD3[i]:
                    if i==0:
                        img.draw_rectangle(b.rect(),color = (255,152,152))
                    elif i==1:
                        img.draw_rectangle(b.rect(),color = (152,255,152))
                    elif i==2:
                        img.draw_rectangle(b.rect(),color = (152,152,255))
                    img.draw_cross(b.cx(), b.cy())
                pass
            else:
                BlobStateSAD3[i] = 0
        for i in range(3):
            if BlobStateSAD3[i] != 0:
                finishFlag = finishFlag+1
    #接下来识别每个区域内的颜色
    #-SAD1
    for i in range(3):
        if BlobStateSAD1[i]!= 0:
            AREA2COLOR[0]=i+1
    #-SAD2
    for i in range(3):
        if BlobStateSAD2[i]!= 0:
            AREA2COLOR[1]=i+1
    #-SAD3
    for i in range(3):
        if BlobStateSAD3[i]!= 0:
            AREA2COLOR[2]=i+1
    #打印内容
    for i in AREA2COLOR:
        uart.write(str(i))
    print(AREA2COLOR)

#决赛-六物料识别程序
def FinalColorDetect():
    print("Final Color Detect\n")
    GetBlobStateUp()
    GetColorPositionUp()
    GetBlobStateDown()
    GetColorPositionDown()
    print("Color Position Up:",ColorPositionUp)
    print("Color Position Down:",ColorPositionDown)
    Sendcode()

#将发送给OpenMV的所有数据进行打印
def PikaTransform():
    print("Pika Transform\n")
    while True:
        if uart.any():
            DataRecieved = uart.read()
            DataRecieved = str(DataRecieved)
            print(DataRecieved)

#通用型发送程序
def TSendCode(CodeGroup):
    for i in CodeGroup:
        uart.write(str(i))

#通用型位置码转换程序
def TTransform(PositionGroup):
    codetrans=[0,0,0]
    for i in PositionGroup:
        codetrans[PositionGroup[i]] = i
    return codetrans


#决赛-发送台阶识别内容
def Sendcode():
    global ColorPositionDown, ColorPositionUp
    print("Send Code\n")
    i = 0
    codetempdown=[0,0,0]
    codetempup=[0,0,0]
    for i in ColorPositionDown:
        codetempdown[ColorPositionDown[i]] = i
    for i in ColorPositionUp:
        codetempup[ColorPositionUp[i]] = i
    LED(1).on()
    LED(3).on()
    for i in codetempdown:
        uart.write(str(i+1))
        print(i)
    for i in codetempup:
        uart.write(str(i+1))
        print(i)
    time.sleep(2)
    LED(1).off()
    LED(3).off()

#决赛-备用程序-台阶抓取
def FinalCVCapture():
    global ColorReference, ColorPositionUp, ColorPositionDown, ColorCode2, ColorCode1
    print("Final CV Capture\n")
    #上台阶
    sleeptime0 = 2.6#左
    sleeptime1 = 2.1#中
    sleeptime2 = 2.6#右
    #下台阶
    sleeptime3 = 2.6#左
    sleeptime4 = 2.1#中
    sleeptime5 = 2.6#右
    #放置
    sleeptimeput = 8
    #先夹取第一层
    if Round == 1:
        #获取颜色位置
        FinalColorDetect()
        for i in range(3):
            print("FCV-Want Color is", ColorCode1[i])
            if ColorCode1[i] == 0:
                fcposition=ColorPositionUp[0]
                uart.write(str(fcposition))
                LED(2).off()
                LED(1).on()
                if fcposition == 0:
                    time.sleep(sleeptime0)
                elif fcposition == 1:
                    time.sleep(sleeptime1)
                elif fcposition == 2:
                    time.sleep(sleeptime2)
                LED(1).off()
                LED(2).on()
            elif ColorCode1[i] == 1:
                fcposition=ColorPositionUp[1]
                uart.write(str(fcposition))
                LED(2).off()
                LED(1).on()
                if fcposition == 0:
                    time.sleep(sleeptime0)
                elif fcposition == 1:
                    time.sleep(sleeptime1)
                elif fcposition == 2:
                    time.sleep(sleeptime2)
                LED(1).off()
                LED(2).on()
            elif ColorCode1[i] == 2:
                fcposition=ColorPositionUp[2]
                uart.write(str(fcposition))
                LED(2).off()
                LED(1).on()
                if fcposition == 0:
                    time.sleep(sleeptime0)
                elif fcposition == 1:
                    time.sleep(sleeptime1)
                elif fcposition == 2:
                    time.sleep(sleeptime2)
            if ColorCode1[i] == 0:
                print("And Now Put It At Red")
                LED(2).off()
                LED(1).on()
                uart.write(str('R'))
            elif ColorCode1[i] == 1:
                print("And Now Put It At Green")
                LED(2).off()
                LED(1).on()
                uart.write(str('G'))
            elif ColorCode1[i] == 2:
                print("And Now Put It At Blue")
                LED(2).off()
                LED(1).on()
                uart.write(str('B'))
            time.sleep(sleeptimeput)
    #再夹取第二层
    if Round == 2:
        #第二遍就不要再识别了，直接控制
        for i in range(3):
            print("FCV-Want Color is", ColorCode2[i])
            if ColorCode2[i] == 0:
                fcposition=ColorPositionDown[0]
                uart.write(str(fcposition))
                LED(2).off()
                LED(1).on()
                if fcposition == 0:
                    time.sleep(sleeptime3)
                elif fcposition == 1:
                    time.sleep(sleeptime4)
                elif fcposition == 2:
                    time.sleep(sleeptime5)
                LED(1).off()
                LED(2).on()
            if ColorCode2[i] == 1:
                fcposition=ColorPositionDown[1]
                uart.write(str(fcposition))
                LED(2).off()
                LED(1).on()
                if fcposition == 0:
                    time.sleep(sleeptime3)
                elif fcposition == 1:
                    time.sleep(sleeptime4)
                elif fcposition == 2:
                    time.sleep(sleeptime5)
                LED(1).off()
                LED(2).on()
            if ColorCode2[i] == 2:
                fcposition=ColorPositionDown[2]+3
                uart.write(str(fcposition))
                LED(2).off()
                LED(1).on()
                if fcposition == 0:
                    time.sleep(sleeptime3)
                elif fcposition == 1:
                    time.sleep(sleeptime4)
                elif fcposition == 2:
                    time.sleep(sleeptime5)
                LED(1).off()
                LED(2).on()
            if ColorCode2[i] == 0:
                print("And Now Put It At Red")
                LED(2).off()
                LED(1).on()
                uart.write(str('R'))
            elif ColorCode2[i] == 1:
                print("And Now Put It At Green")
                LED(2).off()
                LED(1).on()
                uart.write(str('G'))
            elif ColorCode2[i] == 2:
                print("And Now Put It At Blue")
                LED(2).off()
                LED(1).on()
                uart.write(str('B'))
            time.sleep(sleeptimeput)

#以VGA分辨率启动摄像头
def CameraStartupHD():
    print("Camera Startup HD\n")
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.VGA)
    sensor.set_windowing((320, 240))
    sensor.skip_frames(time = 200)

def CameraStartupHDFree():
    print("Camera Startup HD Free\n")
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.VGA)
    sensor.skip_frames(time = 200)

#阈值显示器
def ColorThresholds():
    print("Color Thresholds\n")
    print("Enter any key to quit\n")
    Color=["Red","Green","Blue"]
    while True:
        img = sensor.snapshot().lens_corr(1.8)
        for i in range(3):
            #flag = 0
            blobs = img.find_blobs(color_thresholds[i],pixels_threshold = pixels_threshold,area_threshold = area_threshold,merge = True)
            if blobs:
                for b in blobs:
                    if i==0:
                        img.draw_rectangle(b.rect(),color = (255,152,152))
                    elif i==1:
                        img.draw_rectangle(b.rect(),color = (152,255,152))
                    elif i==2:
                        img.draw_rectangle(b.rect(),color = (152,152,255))
                    img.draw_cross(b.cx(), b.cy())
        if uart.any():
            break

#接受传输数据
def GetCode():
    print("Get Code\n")
    global DataRecieved,ColorCode1,ColorCode2
    DataRecieved = 0
    FLAG = 0
    while FLAG != 6:
        if uart.any():
            DataRecieved = uart.read()
            DataRecieved = str(DataRecieved)
            print(DataRecieved)
            for i in range(0, 3):
                ColorCode1[i] = int(DataRecieved[2+i])-1
                FLAG += 1
                print(ColorCode1[i])
            for i in range(0, 3):
                ColorCode2[i] = int(DataRecieved[5+i])-1
                FLAG += 1
                print(ColorCode2[i])

#通用库程序，通过传入的rroi获取Blobs状态。
def TBlobState(rroi):
    global BlobStateTemp,color_thresholds,pixels_threshold,area_threshold
    BlobStateTemp = [0,0,0]
    img = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        BlobStateTemp[i] = img.find_blobs(color_thresholds[i],pixels_threshold = pixels_threshold,area_threshold = area_threshold,merge = True, roi=rroi)
        if BlobStateTemp[i]:
            pass
        else:
            BlobStateTemp[i] = 0

def UniBlobState(RefenrenceThresholds,rroi):
    global BlobStateTemp,color_thresholds,pixels_threshold,area_threshold
    BlobStateTemp = [0,0,0]
    img = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        BlobStateTemp[i] = img.find_blobs(RefenrenceThresholds[i],pixels_threshold = pixels_threshold,area_threshold = area_threshold,merge = True, roi=rroi)
        if BlobStateTemp[i]:
            pass
        else:
            BlobStateTemp[i] = 0

#获取当前帧Blobs状态
def GetBlobState():
    ## 非细调阈值测试别开，会很吵
    ## print("Get Blob State\n")
    global BlobState,color_thresholds,pixels_threshold,area_threshold
    BlobState = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobState[i] = img.find_blobs(color_thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if BlobState[i]:
            for b in BlobState[i]:
                if i==0:
                    img.draw_rectangle(b.rect(),color = (255,152,152))
                elif i==1:
                    img.draw_rectangle(b.rect(),color = (152,255,152))
                elif i==2:
                    img.draw_rectangle(b.rect(),color = (152,152,255))
                img.draw_cross(b.cx(), b.cy())
            pass
        else:
            BlobState[i] = 0
        #此处返回的BlobState[i]是一个列表，列表中每个元素都是一个二维列表，每个二维列表都是一个Blob对象。
        #其中，0号元素是红色的Blob对象，1号元素是绿色的Blob对象，2号元素是蓝色的Blob对象。
        #Blob对象中，0号元素是Blob的中心点，1号元素是Blob的面积，2号元素是Blob的颜色，3号元素是Blob的旋转角度，4号元素是Blob的旋转中心点，5号元素是Blob的旋转中心点的颜色。
        #举例：红色对象为BlobState[0]。Blob对象的操作参考：https://book.openmv.cc/image/blob.html
    ## 非细调阈值测试别开，会很吵
    ## print(BlobState)

#低位置圆盘识别
def GetBlobStateLow():
    ## 非细调阈值测试别开，会很吵
    ## print("Get Blob State\n")
    global BlobStateLow,color_thresholds,pixels_threshold,area_threshold,roiLow
    BlobStateLow = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateLow[i] = img.find_blobs(color_thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True, roi=roiLow)
        if BlobStateLow[i]:
            pass
        else:
            BlobStateLow[i] = 0
        #此处返回的BlobState[i]是一个列表，列表中每个元素都是一个二维列表，每个二维列表都是一个Blob对象。
        #其中，0号元素是红色的Blob对象，1号元素是绿色的Blob对象，2号元素是蓝色的Blob对象。
        #Blob对象中，0号元素是Blob的中心点，1号元素是Blob的面积，2号元素是Blob的颜色，3号元素是Blob的旋转角度，4号元素是Blob的旋转中心点，5号元素是Blob的旋转中心点的颜色。
        #举例：红色对象为BlobState[0]。Blob对象的操作参考：https://book.openmv.cc/image/blob.html
    ## 非细调阈值测试别开，会很吵
    ## print(BlobState)

#决赛圆盘颜色探测
def GetBlobStateTarget():
    ## 非细调阈值测试别开，会很吵
    ## print("Get Blob State\n")
    global BlobStateTarget,TargetThresholds,TargetPix,TargetArea,roiTarget
    CameraStartupHDFree()
    BlobStateTarget = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateTarget[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=TargetPix, area_threshold=TargetArea, merge=True, roi=roiTarget)
        if BlobStateTarget[i]:
            for b in BlobStateTarget[i]:
                if i==0:
                    img.draw_rectangle(b.rect(),color = (255,152,152))
                elif i==1:
                    img.draw_rectangle(b.rect(),color = (152,255,152))
                elif i==2:
                    img.draw_rectangle(b.rect(),color = (152,152,255))
                img.draw_cross(b.cx(), b.cy())
            pass
        else:
            BlobStateTarget[i] = 0
        #此处返回的BlobState[i]是一个列表，列表中每个元素都是一个二维列表，每个二维列表都是一个Blob对象。
        #其中，0号元素是红色的Blob对象，1号元素是绿色的Blob对象，2号元素是蓝色的Blob对象。
        #Blob对象中，0号元素是Blob的中心点，1号元素是Blob的面积，2号元素是Blob的颜色，3号元素是Blob的旋转角度，4号元素是Blob的旋转中心点，5号元素是Blob的旋转中心点的颜色。
        #举例：红色对象为BlobState[0]。Blob对象的操作参考：https://book.openmv.cc/image/blob.html
    ## 非细调阈值测试别开，会很吵
    ## print(BlobState)

#台阶上物料识别
def GetBlobStateUp():
    global BlobStateUp,color_thresholds,pixels_threshold,area_threshold,roiUp
    BlobStateUp = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateUp[i] = img.find_blobs(color_thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True, roi=roiUp)
        if BlobStateUp[i]:
            for b in BlobStateUp[i]:
                if i==0:
                    img.draw_rectangle(b.rect(),color = (255,152,152))
                elif i==1:
                    img.draw_rectangle(b.rect(),color = (152,255,152))
                elif i==2:
                    img.draw_rectangle(b.rect(),color = (152,152,255))
                img.draw_cross(b.cx(), b.cy())
            pass
        else:
            BlobStateUp[i] = 0
    # print(BlobStateUp)

#台阶下物料识别
def GetBlobStateDown():
    global BlobStateDown,color_thresholds,pixels_threshold,area_threshold,roiDown
    BlobStateDown = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateDown[i] = img.find_blobs(color_thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True, roi=roiDown)
        if BlobStateDown[i]:
            for b in BlobStateDown[i]:
                if i==0:
                    img.draw_rectangle(b.rect(),color = (255,152,152))
                elif i==1:
                    img.draw_rectangle(b.rect(),color = (152,255,152))
                elif i==2:
                    img.draw_rectangle(b.rect(),color = (152,152,255))
                img.draw_cross(b.cx(), b.cy())
            pass
        else:
            BlobStateDown[i] = 0
    # print(BlobStateDown)

#识别前一个圆盘靶
def GetBlobStateFF():
    global BlobStateFF,TargetThresholds,TargetPix,TargetArea,roiFF
    BlobStateFF = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateFF[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=TargetPix, area_threshold=TargetArea, merge=True, roi=roiFF)
        if BlobStateFF[i]:
            pass
        else:
            BlobStateFF[i] = 0

#识别后一个圆盘靶
def GetBlobStateBB():
    global BlobStateBB,TargetThresholds,TargetPix,TargetArea,roiFF
    BlobStateBB = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateBB[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=TargetPix, area_threshold=TargetArea, merge=True, roi=roiBB)
        if BlobStateBB[i]:
            pass
        else:
            BlobStateBB[i] = 0

#识别指定位置物料（是否为空）
def GetBlobEmpty():
    global BlobStateEmpty,TargetThresholds,EmptyPix,EmptyArea,roiFF,roiBB,CVShootMode
    BlobStateEmpty = [0,0,0]
    #拍摄一张照片
    img = sensor.snapshot().lens_corr(1.5)
    #更新此帧Blobs状态。
    for i in range(3):# 0-红色，1-绿色，2-蓝色
        BlobStateEmpty[i] = img.find_blobs(TargetThresholds[i], pixels_threshold=EmptyPix, area_threshold=EmptyArea, merge=True, roi=roiBB)
        if BlobStateEmpty[i]:
            pass
        else:
            BlobStateEmpty[i] = 0
        for b in BlobStateEmpty[i]:
            if i==0:
                img.draw_rectangle(b.rect(),color = (255,152,152))
            elif i==1:
                img.draw_rectangle(b.rect(),color = (152,255,152))
            elif i==2:
                img.draw_rectangle(b.rect(),color = (152,152,255))
            img.draw_cross(b.cx(), b.cy())

#通过找圆的方式判断是否静止
def FinalIfStop():
    global CircleState, StopThreshold, roiCircle
    CameraStartupHDFree()
    CircleState1 = 0
    CircleState2 = 0
    GetCircleState(roiCircle)
    CircleState1 = CircleState
    time.sleep_ms(300)
    GetCircleState(roiCircle)
    CircleState2 = CircleState
    stillflag = False
    if CircleState1 == 0:
        print("No circle1?")
    elif CircleState2 == 0:
        print("No circle2?")
    elif abs(int(CircleState1[0].x())-int(CircleState2[0].x()))<=StopThreshold:
        print("FS-Move")
        stillflag = True
    else:
        print("FS-Still")
    return stillflag

#通过找圆的方式判断是否移动
def FinalIfMove():
    global CircleState, MoveThreshold, roiCircle
    CameraStartupHDFree()
    CircleState1 = 0
    CircleState2 = 0
    GetCircleState(roiCircle)
    CircleState1 = CircleState
    time.sleep_ms(300)
    GetCircleState(roiCircle)
    CircleState2 = CircleState
    stillflag = False
    if CircleState1 == 0:
        print("No circle1?")
    elif CircleState2 == 0:
        print("No circle2?")
    elif abs(int(CircleState1[0].x())-int(CircleState2[0].x()))> MoveThreshold:
        print("FS-Move")
        stillflag = True
    else:
        print("FS-Still")
    return stillflag


#圆盘位置检测程序
def CheckDiskPosition():
    print("Check Disk Position\n")
    #更新当前帧Blobs状态。
    GetBlobState()
    #循环到只出现一个颜色的Blob对象。
    while True:
        BlobCount = 0 #计数Blob对象个数
        for i in range(3):
            if BlobState[i] != 0:#非初始值
                BlobCount += 1 #检测到一个颜色
                print("CDP01-GetBlob")
        #唯有出现一个颜色时
        if BlobCount == 1:
            print("CDP01-Exit")
            break
        else:
            GetBlobState()#检测到多个颜色，重新获取Blobs状态。
            print("Check Disk Position 01\n")
    #退出循环时，只有一个颜色的Blob对象。
    #此时需要检测是否出现两个颜色的Blob对象。两个以上(考虑到运动产生杂色)的颜色出现，代表此时圆盘正在转动。
    while True:
        BlobCount = 0 #计数Blob对象个数
        for i in range(3):
            if BlobState[i]!= 0:#非初始值
                BlobCount += 1 #检测到一个颜色
        #出现两个颜色时
        if BlobCount == 2:
            break
        else:
            GetBlobState() #检测到多个颜色，重新获取Blobs状态。
            print("Check Disk Position 02\n")
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
            print("Check Disk Position 03\n")
    print("Check Disk Position Finished\n")

#圆盘夹取程序
def GetDisk():
    print("Get Disk\n")
    global ColorCode1,ColorCode2,Round
    CurrentColor=3
    #确定当前轮数的颜色参考组。
    ColorReference=[0,0,0]
    print("Round is", Round)
    if Round == 1:
        ColorReference = ColorCode1
    else:
        ColorReference = ColorCode2
    DiskGotCount = 0 #计数，当前取到了几个物料
    stillflagpub = 0
    while DiskGotCount < 3:
        stillflagpub = 0 #0-静止，1-运动
        while CheckStopStatic():
            continue
        print("GD-STEP 1")
        while CheckMotionStatic():
            continue
        print("GD-STEP 2")
        #获取当前帧Blobs状态。
        GetBlobStateLow()
        #确认当前位置的颜色。
        for i in range(3):
            if BlobStateLow[i] != 0:
                CurrentColor = i
        #查看当前轮数。轮数1则令颜色参考组为1，否则为2.
        #根据颜色指挥下位机夹取对应物料。
        if CurrentColor == ColorReference[DiskGotCount]:
            print("ColorReference is", ColorReference)
            print("Want Color is:",ColorReference[DiskGotCount])
            if CurrentColor == 0: #0-红色
                print("Current Capturing Is Red")
                uart.write(str('R'))
                DiskGotCount += 1
                time.sleep(10.5)
            elif CurrentColor == 1: #1-绿色
                print("Current Capturing Is Green")
                uart.write(str('G'))
                DiskGotCount += 1
                time.sleep(10.5)
            elif CurrentColor == 2: #2-蓝色
                print("Current Capturing Is Blue")
                uart.write(str('B'))
                DiskGotCount += 1
                time.sleep(10.5)
        #通过固定延时等待圆盘转到下一个物料。

#新版圆盘夹取程序
#警告，警告，改变动作组时间需要同步更改Arduino中的内容
def GetDiskNew():
    print("Get Disk New\n")
    global ColorPosition,Round,ColorCode1,ColorCode2
    #获取当前帧Blobs状态。
    #确定当前轮数的颜色参考组。
    ColorReference=[0,0,0]
    if Round == 1:
        ColorReference = ColorCode1
    else:
        ColorReference = ColorCode2
    #按照ColorReference的顺序夹取对应物料
    for i in range(3):
        #每过一次都要更新一下Blobs状态。
        #第零步：直到画面开始移动
        while CheckStopStatic():
            continue
        print("GDN-STEP 1")
        while CheckMotionStatic():
            continue
        print("GDN-STEP 2")
        GetBlobState()
        LED(2).off()
        LED(1).on()
        #更新位置表
        GetColorPosition()
        print("GDN-Want Color is", ColorReference[i])
        if ColorReference[i] == 0:#要夹的是红色
            #调取红色的位置是？
            cposition=ColorPosition[0]
            print("And Its Position is", cposition)
            #将其传递给下位机
            uart.write(str(cposition))
            LED(2).off()
            LED(1).on()
            if cposition == 0:
                time.sleep(1.1)
            elif cposition == 1:
                time.sleep(1.1)
            elif cposition == 2:
                time.sleep(1.1)
            LED(1).off()
            LED(2).on()
        elif ColorReference[i] == 1:#要夹的是绿色
            cposition=ColorPosition[1]
            print("And Its Position is", cposition)
            uart.write(str(cposition))
            LED(2).off()
            LED(1).on()
            if cposition == 0:
                time.sleep(1.1)
            elif cposition == 1:
                time.sleep(1.1)
            elif cposition == 2:
                time.sleep(1.1)
            LED(1).off()
            LED(2).on()
        elif ColorReference[i] == 2:#要夹的是蓝色
            cposition=ColorPosition[2]
            print("And Its Position is", cposition)
            uart.write(str(cposition))
            LED(2).off()
            LED(1).on()
            if cposition == 0:
                time.sleep(1.1)
            elif cposition == 1:
                time.sleep(1.1)
            elif cposition == 2:
                time.sleep(1.1)
            LED(1).off()
            LED(2).on()
        if ColorReference[i] == 0:
            print("And Now Put It At Red")
            LED(2).off()
            LED(1).on()
            uart.write(str('R'))
        if ColorReference[i] == 1:
            print("And Now Put It At Green")
            LED(2).off()
            LED(1).on()
            uart.write(str('G'))
        if ColorReference[i] == 2:
            print("And Now Put It At Blue")
            LED(2).off()
            LED(1).on()
            uart.write(str('B'))
        time.sleep(4.3)#放置动作需要时间
        LED(1).off()
        LED(2).on()
'''
def FinalPutDisk():
    for i in range(3):'''

#圆盘识别程序
def CVDisk():
    print("CV Disk\n")
    #第一步：确定圆盘是否停稳了。
    ## CheckDiskPosition()
    #第二步：根据接收到的数据指挥下位机按顺序夹取对应物料
    GetDisk()

#新版圆盘识别程序
def CVDiskNew():
    print("CV Disk New\n")
    #第二步：根据位置表指挥下位机按顺序夹取对应物料
    GetDiskNew()

#检测当前画面是否运动
def CheckMotionStatic():
    ## print("Check Motion Static\n")
    #公有变量，表示两帧差距阈值，超出该值视为运动
    global MoveThreshold, BlobState
    #私有变量，储存用于对比的第一帧Blobs状态
    BlobState1 = [0,0,0]
    #以及第二帧
    BlobState2 = [0,0,0]
    #更新当前帧Blobs状态。
    GetBlobState()
    #此处更新BlobState1
    BlobState1=BlobState
    #再次获取当前帧Blobs状态。
    time.sleep_ms(300)
    GetBlobState()
    #此处更新BlobState2
    BlobState2=BlobState
    ##测试
    ## print("BlobState1.red.cx:",BlobState1[0][0][5])
    ## print("BlobState2.red.cx:",BlobState2[0][0][5])
    #若两帧Blobs状态（红色x轴坐标值、绿色x轴坐标值、蓝色x轴坐标值）差距小于阈值，则认为静止。
    stillflag = False
    for i in range(3):
        ## print("Current Check Color is:",i)
        if BlobState1[i] == 0:
            ## print("Color Code Not Found:", i)
            continue
        elif BlobState2[i] == 0:
            ## print("Color Code 2 Not Found:", i)
            continue
        elif abs(int(BlobState1[i][0].cx()) - int(BlobState2[i][0].cx())) > MoveThreshold:
            ## print("Color Code Found Stop:",i)
            stillflag = True
        else:
            ## print("Detect Moving...")
            continue
    ## print("Moving Flag is:", stillflag)
    return stillflag #只有当静止时，程序返回True。否则（动时）返回False。

def CheckStopStatic():
    ## print("Check Motion Static\n")
    #公有变量，表示两帧差距阈值，超出该值视为运动
    global StopThreshold, BlobState
    #私有变量，储存用于对比的第一帧Blobs状态
    BlobState1 = [0,0,0]
    #以及第二帧
    BlobState2 = [0,0,0]
    #更新当前帧Blobs状态。
    GetBlobState()
    #此处更新BlobState1
    BlobState1=BlobState
    #再次获取当前帧Blobs状态。
    time.sleep_ms(100)
    GetBlobState()
    #此处更新BlobState2
    BlobState2=BlobState
    ##测试
    ## print("BlobState1.red.cx:",BlobState1[0][0][5])
    ## print("BlobState2.red.cx:",BlobState2[0][0][5])
    #若两帧Blobs状态（红色x轴坐标值、绿色x轴坐标值、蓝色x轴坐标值）差距小于阈值，则认为静止。
    stillflag = False
    for i in range(3):
        ## print("Current Check Color is:",i)
        if BlobState1[i] == 0:
            ## print("Color Code Not Found:", i)
            continue
        elif BlobState2[i] == 0:
            ## print("Color Code 2 Not Found:", i)
            continue
        elif abs(int(BlobState1[i][0].cx()) - int(BlobState2[i][0].cx())) <= 2:
            ## print("Color Code Found Stop:",i)
            stillflag = True
        else:
            ## print("Detect Moving...")
            continue
    ## print("Moving Flag is:", stillflag)
    return stillflag #只有当静止时，程序返回True。否则（动时）返回False。

#圆阈值显示器
def CircleThresholds():
    global DetectThreshold,RMIN,RMAX,roiCircle
    print("Circle Thresholds\n")
    while True:
        img = sensor.snapshot().lens_corr(1.8)
        for c in img.find_circles(
        threshold=DetectThreshold,
        x_margin=20,
        y_margin=20,
        r_margin=30,
        r_min=RMIN,
        r_max=RMAX,
        r_step=2,
        roi=roiCircle
        ):
            img.draw_circle(c.x(), c.y(), c.r(), color=(255, 0, 0))
            img.draw_cross(c.x(),c.y())
            print(c)

def GetCircleState(roic):
    global CircleState, DetectThreshold, RMIN,  RMAX,Xstart,Xend
    CircleState = 0
    img = sensor.snapshot().lens_corr(1.8)
    CircleState = img.find_circles(
        threshold=DetectThreshold,
        x_margin=20,
        y_margin=20,
        r_margin=30,
        r_min=RMIN,
        r_max=RMAX,
        r_step=2,
        roi=roic
        )
    if CircleState:
        pass
    else:
        CircleState=0
    # print("CircleStateis",CircleState)

#圆定位
def Navigation():
    global DetectThreshold,RMIN,RMAX,Xstart,Xend
    print("Navigation\n")
    endflag = 0
    while True:
        img = sensor.snapshot().lens_corr(1.8)
        for c in img.find_circles(
        threshold=DetectThreshold,
        x_margin=20,
        y_margin=20,
        r_margin=30,
        r_min=RMIN,
        r_max=RMAX,
        r_step=2,
        ## roi=roi
        ):
            print("Circle at Position",c.x())
            img.draw_circle(c.x(), c.y(), c.r(), color=(255, 0, 0))
            img.draw_cross(c.x(),c.y())
            if c.x() > Xstart and c.x() < Xend:
                uart.write(str('C'))
                print("XCenter GOT")
                endflag += 1
            elif c.x() > Xend:
                uart.write(str('L'))
                print("Now at Right, Move Left")
            elif c.x() < Xstart:
                uart.write(str('R'))
                print("Now at Left, Move Right")
        if endflag >= 3:
            print("Position Confirmed")
            uart.write(str('E'))
            break

#决赛-打靶
def FinalCVShooting():
    global BlobStateTartget,ColorCode1,ColorCode2,Round,MissCount
    print("Final CV Shooting\n")
    waitimeR = 0 #夹取R时间
    waitimeG = 0 #夹取G时间
    waitimeB = 0 #夹取B时间
    waitimePut = 0 #放置时间
    waitimeThrow = 0 #丢弃时间
    #根据轮数更新颜色参考值
    ColorReference=[0,0,0]
    if Round == 1:
        ColorReference = ColorCode1
    else:
        ColorReference = ColorCode2
    #遍历三个顺位
    for cr in ColorReference:
        #先夹取
        if cr == 0:
            uart.write(str('R'))
            time.sleep(waitimeR)
            print("FCV-WantColorRed")
        elif cr == 1:
            uart.write(str('G'))
            time.sleep(waitimeG)
            print("FCV-WantColorGreen")
        elif cr == 2:
            uart.write(str('B'))
            time.sleep(waitimeB)
            print("FCV-WantColorBlue")
        ccolor = 0
        miss = 0
        #再判断
        while miss < MissCount: #若超过MissCount次（全局变量），丢弃
            #判断由动到静
            while FinalIfStop():
                continue
            print("FCV-Step1")
            while FinalIfMove():
                continue
            print("FCV-Step2")
            #判断当前颜色
            ccount = 0
            while ccount != 1:#当识别到的颜色超过1种，也不行。没识别到也不行。
                ccount = 0
                GetBlobStateTarget()
                for i in range(3):
                    if BlobStateTarget[i] != 0:
                        ccount += 1 #识别到几种颜色就加多少
                        ccolor = i
                print("FCV-CColor",ccolor)
            #当前颜色与参考颜色相等，则放置并退出循环。
            if cr == ccolor:
                uart.write(str('1'))
                print("Shoot!")
                time.sleep(waitimePut)
                break
            #当前颜色与参考颜色不相等，等待并增加计数。
            else:
                miss +=1
        #若是触碰边界条件退出的，说明miss次数达到MissCount，那就丢弃。
        if miss >= MissCount:
            uart.write(str('0'))#等待超过轮数，丢弃
            time.sleep(waitimeThrow)

#决赛-打靶快速版
def FinalCVShootingFast():
    #CVShootMode:1-前一个（逆时针），2-后一个,3-本位（不进行等待）
    global BlobStateTartget,ColorCode1,ColorCode2,Round,MissCount
    print("Final CV Shooting\n")
    waitimeR = 0 #夹取R时间
    waitimeG = 0 #夹取G时间
    waitimeB = 0 #夹取B时间
    waitimePut = 0 #放置时间
    #根据轮数更新颜色参考值
    ColorReference=[0,0,0]
    if Round == 1:
        ColorReference = ColorCode1
    else:
        ColorReference = ColorCode2
    #遍历三个顺位
    for cr in ColorReference:
        #先夹取
        if cr == 0:
            uart.write(str('R'))
            time.sleep(waitimeR)
        elif cr == 1:
            uart.write(str('G'))
            time.sleep(waitimeG)
        elif cr == 2:
            uart.write(str('B'))
            time.sleep(waitimeB)
        #判断由动到静
        while FinalIfStop():
            continue
        print("FCV-Step1")
        while FinalIfMove():
            continue
        print("FCV-Step2")
        uart.write(str('1'))
        time.sleep(waitimePut)

#通用程序，传入Blobs状态，返回颜色位置表
def TColorPosition(InBlobState):
    print("TColorPosition\n")
    global ColorPositionTemp,XTH01,XTH12
    for i in range(3):
        if InBlobState[i] == 0:
            ColorPositionTemp[i]=3
        elif InBlobState[i][0].cx()<=XTH0:
            ColorPositionTemp[i]=0
        elif InBlobState[i][0].cx()<=XTH12:
            ColorPositionTemp[i]=1
        else:
            ColorPositionTemp[i]=2
    print("Color Position is",ColorPositionTemp)

#将识别颜色与位置表相连
def GetColorPosition():
    print("Get Color Position\n")
    #请先确保ColorCode1和ColorCode2已被赋值，且获取过Blobs状态。
    global ColorPosition,BlobState,XTH01,XTH12
    for i in range(3):
        #如果BlobStatr[i]不存在
        # print("Current Check Color is:",i)
        if BlobState[i] == 0:
            ColorPosition[i]=3
            # print("Color Code Not Found ?")
        elif BlobState[i][0].cx()<=XTH01:
            ColorPosition[i]=0
            # print("Color Code at Position 0")
        elif BlobState[i][0].cx()<=XTH12:
            ColorPosition[i]=1
            # print("Color Code at Position 1")
        else:
            # print("Color Code at Position 2")
            ColorPosition[i]=2
    print("ColorPosition  of Red/Green/Blue is",ColorPosition)

def GetColorPositionUp():
    print("Get Color Position UP\n")
    #请先确保ColorCode1和ColorCode2已被赋值，且获取过Blobs状态。
    global ColorPositionUp,BlobStateUp,FTH01,FTH12
    for i in range(3):
        #如果BlobStatr[i]不存在
        # print("Current Check Color is:",i)
        while True:
            print("GetPositionUp-BlobCheck")
            if BlobStateUp[0] == 0:
                print("Color Code Not Found?Retry")
                GetBlobStateUp()
                continue
            elif BlobStateUp[1] == 0:
                print("Color Code Not Found?Retry")
                GetBlobStateUp()
                continue
            elif BlobStateUp[2] == 0:
                print("Color Code Not Found?Retry")
                GetBlobStateUp()
                continue
            else:
                break
        if BlobStateUp[i][0].cx()<=FTH01:
            ColorPositionUp[i]=0
            # print("Color Code at Position 0")
        elif BlobStateUp[i][0].cx()<=FTH12:
            ColorPositionUp[i]=1
            # print("Color Code at Position 1")
        else:
            # print("Color Code at Position 2")
            ColorPositionUp[i]=2
    print("FUp-ColorPosition  of Red/Green/Blue is",ColorPosition)

def GetColorPositionDown():
    print("Get Color Position Down\n")
    #请先确保ColorCode1和ColorCode2已被赋值，且获取过Blobs状态。
    global ColorPositionDown,BlobStateDown,FTH01,FTH12
    for i in range(3):
        while True:
            print("GetPositionDown-BlobCheck")
            if BlobStateDown[0] == 0:
                GetBlobStateDown()
                continue
            elif BlobStateDown[1] == 0:
                GetBlobStateDown()
                continue
            elif BlobStateDown[2] == 0:
                GetBlobStateDown()
                continue
            else:
                break
        # print("Current Check Color is:",i)
        if BlobStateDown[i][0].cx()<=FTH01:
            ColorPositionDown[i]=0
            # print("Color Code at Position 0")
        elif BlobStateDown[i][0].cx()<=FTH12:
            ColorPositionDown[i]=1
            # print("Color Code at Position 1")
        else:
            # print("Color Code at Position 2")
            ColorPositionDown[i]=2
    print("FDown-ColorPosition  of Red/Green/Blue is",ColorPosition)



#自由打靶程序
def CVShooting():
    print("CV Shooting\n")
    global ColorPosition,ColorCode1,ColorCode2,BlobState,Round
    #获取当前帧Blobs状态。
    GetBlobState()
    #获取颜色位置
    GetColorPosition()
    #将颜色位置进行汇报


#主程序
while True:
    LED(3).on()
    ##测试脚手架
    Lighting.low()
    CameraStartupHDFree()
    '''while True:
        FinalCVShooting()'''
    ##测试脚手架结束
    ##哈咯哈咯
    # Lighting.low()
    CameraStartup()
    ColorThresholds()
    if (uart.any()):
        #选择运行模式
        ModeSelect = uart.read()
        LED(3).off()
        LED(2).on()
        Lighting.low()
        print("ModeSelect is:",ModeSelect)
        if ModeSelect == b'c':#模式选择：c-扫码传输颜色组
            GetCode()
        elif ModeSelect == b'f': #模式选择：f-旧版圆盘识别
            Round=1
            while ColorCode1==[0,0,0]:
                print("Get Code First Then Enter. Please Restart.")
                time.sleep(1)
            CameraStartup()
            CVDisk() #圆盘识别程序
            uart.write(str('j')) #在下位机中定义的阶段停止标志
        elif ModeSelect == b'r': #模式选择：r-第二次旧版圆盘识别，程序相同
            Round=2
            CameraStartup()
            CVDisk()
            uart.write(str('s'))
        elif ModeSelect == b's': #模式选择：s-新版圆盘识别
            Round=1
            CameraStartup()
            CVDiskNew()
            uart.write(str('j'))
        elif ModeSelect == b'b': #模式选择：b-第二次新版圆盘识别，程序相同
            Round=2
            CameraStartup()
            CVDiskNew()
            uart.write(str('s'))
        elif ModeSelect == b'd': #模式选择：d-自由打靶(决赛)
            CameraStartup()
            CVShooting()
            uart.write(str('d'))
        elif ModeSelect == b't': #模式选择：t-传输颜色
            CameraStartup()
            FinalColorDetect()
            Sendcode()
        elif ModeSelect == b'i': #模式选择：i-圆阈值显示器
            CameraStartupHD()
            CircleThresholds()
        elif ModeSelect == b'n': #模式选择：n-导航模式
            CameraStartupHD()
            Navigation()
        elif ModeSelect == b'x': #模式选择：x-决赛物料
            CameraStartup()
            FinalCVCapture()
        elif ModeSelect == b'h': #模式选择：y-决赛打靶
            CameraStartup()
            FinalCVShooting()
        elif ModeSelect == b'g': #模式选择：g-二号区域颜色识别
            #SAD涉及多次初始化，请勿加上CameraStartup()
            FinalSecondAreaDetect()
        Lighting.high()
        LED(2).off()
        LED(3).on()
