import sensor, image, time, math,pyb
from pyb import UART

#颜色阈值
blue = (0, 59, 2, 56, -76, -20)#(0, 29, -40, 35, -97, -5)#(0, 47, -128, 31, -128, -13)
red = (12, 78, 15, 127, 6, 62)#(9, 51, 23, 96, -10, 81)#(14, 40, 18, 52, 1, 127)
green = (12, 61, -78, -12, -40, 55)#(0, 51, -96, -14, -19, 54)
MainBlob = 1000 #定位用的圆阈值

#其他阈值
pixels_threshold = 900 #像素阈值
area_threshold = 100 #面积阈值
MoveThreshold = 5 #移动阈值，用于判断是否移动时的插值
StopThreshold = 5 #停止阈值
color_thresholds = [[red],[green],[blue]] #0-红色，1-绿色，2-蓝色

#定位系统
XCenter = 100#中心点X坐标
YCenter = 100#中心点Y坐标
XThreshold = 10#X轴阈值
YThreshold = 10#Y轴阈值

#公共变量

#-传输到的2组颜色代码
ColorCode1=[0,1,2]
ColorCode2=[1,2,0]

#-当前帧Blobs状态
BlobState = [0,0,0] #注意此变量，全局变量将会在每一次获取Blobs时更新。详情见GetBlobState()
BlobStateLow = [0,0,0] #低位置检测，用于旧版程序

#-颜色组位置
ColorPosition=[0,0,0] #下标为0-红色，1-绿色，2-蓝色，内容对应为0号、1号、2号位置（画面的左、中、右三分之一）

#-当前轮数
Round = 0

# 初始化串口-非调试模式请改成3！！！！！！！！！！！！！！！！！！！！！！！！！！！
uart = UART(3, 115200)

#低位置ROI
roiLow=[70,129,188,109]

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

#阈值显示器
def ColorThresholds():
    print("Color Thresholds\n")
    print("Enter any key to quit\n")
    Color=["Red","Green","Blue"]
    while True:
        img = sensor.snapshot().lens_corr(1.5)
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
            pass
        else:
            BlobState[i] = 0
        #此处返回的BlobState[i]是一个列表，列表中每个元素都是一个二维列表，每个二维列表都是一个Blob对象。
        #其中，0号元素是红色的Blob对象，1号元素是绿色的Blob对象，2号元素是蓝色的Blob对象。
        #Blob对象中，0号元素是Blob的中心点，1号元素是Blob的面积，2号元素是Blob的颜色，3号元素是Blob的旋转角度，4号元素是Blob的旋转中心点，5号元素是Blob的旋转中心点的颜色。
        #举例：红色对象为BlobState[0]。Blob对象的操作参考：https://book.openmv.cc/image/blob.html
    ## 非细调阈值测试别开，会很吵
    ## print(BlobState)

#根据低位置ROI获取当前帧Blobs状态
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
    global MainBlob,MinBlob,MaxBlob
    print("Circle Thresholds\n")
    while True:
        img = sensor.snapshot().lens_corr(1.5)
        center=img.find_circles(threshold = MainBlob, x_margin = 10, y_margin = 10, r_margin = 10,r_min = 2, r_max = 100, r_step = 2)
        for c in center:
            img.draw_circle(c.x(), c.y(), c.r(), color = (255, 0, 0), thickness = 2)
            print(c, c.x(), c.y(), c.r())


#将识别颜色与位置表相连
def GetColorPosition():
    print("Get Color Position\n")
    #请先确保ColorCode1和ColorCode2已被赋值，且获取过Blobs状态。
    global ColorPosition,BlobState
    for i in range(3):
        #如果BlobStatr[i]不存在
        # print("Current Check Color is:",i)
        if BlobState[i] == 0:
            ColorPosition[i]=3
            # print("Color Code Not Found ?")
        elif BlobState[i][0].cx()<=106:
            ColorPosition[i]=0
            # print("Color Code at Position 0")
        elif BlobState[i][0].cx()<=189:
            ColorPosition[i]=1
            # print("Color Code at Position 1")
        else:
            # print("Color Code at Position 2")
            ColorPosition[i]=2
    print("ColorPosition  of Red/Green/Blue is",ColorPosition)

#主程序
while True:
    ##测试脚手架
    '''CameraStartup()
    while True:
        Round = 1
        GetBlobState()
        GetColorPosition()
        time.sleep(0.1)'''
    ##测试脚手架结束
    CameraStartup()
    ColorThresholds()
    ModeSelect = input("Please Select Mode: c-扫码传输颜色组, f-旧版圆盘识别, r-第二次旧版圆盘识别, s-新版圆盘识别\n")
    if (uart.any()):
        #选择运行模式
        ModeSelect = uart.read()
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
            ## uart.write(str('j'))
        elif ModeSelect == b'b': #模式选择：b-第二次新版圆盘识别，程序相同
            Round=2
            CameraStartup()
            CVDiskNew()
            uart.write(str('s'))
        elif ModeSelect == b'd': #模式选择：d-自由打靶(决赛)
            CameraStartup()
            CVShooting()
            uart.write(str('d'))
        elif ModeSelect == b't': #模式选择：t-阈值显示器
            CameraStartup()
            ColorThresholds()
        elif ModeSelect == b'i': #模式选择：i-圆阈值显示器
            CameraStartup()
            CircleThresholds()
        elif ModeSelect == b'y': #模式选择：y-遥控模式
            CameraStartup()
            RemoteControl()

