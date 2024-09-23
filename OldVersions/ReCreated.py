import sensor, image, time, math,pyb
from pyb import UART
from pyb import LED

#颜色阈值
blue = (0, 59, 2, 56, -76, -20)#(0, 29, -40, 35, -97, -5)#(0, 47, -128, 31, -128, -13)
red = (12, 78, 15, 127, 6, 62)#(9, 51, 23, 96, -10, 81)#(14, 40, 18, 52, 1, 127)
green = (12, 61, -78, -12, -40, 55)#(0, 51, -96, -14, -19, 54)

#定位圆阈值
DetectThreshold = 1700 #圆阈值
RMIN = 55 #半径最小值
RMAX = 65 #半径最大值
Xstart = 130 #X轴起始位置
Xend = 150 #X轴结束位置

#其他阈值
pixels_threshold = 900 #像素阈值
area_threshold = 100 #面积阈值
MoveThreshold = 5 #移动阈值，用于判断是否移动时的插值
StopThreshold = 5 #停止阈值
color_thresholds = [[red],[green],[blue]] #0-红色，1-绿色，2-蓝色

#公共变量

#-传输到的2组颜色代码
ColorCode1=[2,2,2]
ColorCode2=[2,2,2]

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

def CameraStartupHD():
    print("Camera Startup HD\n")
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.VGA)
    sensor.set_windowing((320, 240))
    sensor.skip_frames(time = 200)

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
    print("GDN-Round is", Round)
    print("GDN-ColorReference is", ColorReference)
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
                time.sleep(2.6)
            elif cposition == 1:
                time.sleep(2.1)
            elif cposition == 2:
                time.sleep(2.6)
            LED(1).off()
            LED(2).on()
        elif ColorReference[i] == 1:#要夹的是绿色
            cposition=ColorPosition[1]
            print("And Its Position is", cposition)
            uart.write(str(cposition))
            LED(2).off()
            LED(1).on()
            if cposition == 0:
                time.sleep(2.6)
            elif cposition == 1:
                time.sleep(2.1)
            elif cposition == 2:
                time.sleep(2.6)
            LED(1).off()
            LED(2).on()
        elif ColorReference[i] == 2:#要夹的是蓝色
            cposition=ColorPosition[2]
            print("And Its Position is", cposition)
            uart.write(str(cposition))
            LED(2).off()
            LED(1).on()
            if cposition == 0:
                time.sleep(2.6)
            elif cposition == 1:
                time.sleep(2.1)
            elif cposition == 2:
                time.sleep(2.6)
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
        time.sleep(8)#放置动作需要时间
        LED(1).off()
        LED(2).on()

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
    global DetectThreshold,RMIN,RMAX
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
        ## roi=roi
        ):
            img.draw_circle(c.x(), c.y(), c.r(), color=(255, 0, 0))
            img.draw_cross(c.x(),c.y())
            print(c)

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
    ##测试脚手架
    Round=1
    CameraStartupHD()
    CircleThresholds()
    ##测试脚手架结束
    CameraStartup()
    ColorThresholds()
    LED(3).on()
    if (uart.any()):
        #选择运行模式
        ModeSelect = uart.read()
        LED(3).off()
        LED(2).on()
        print("ModeSelect is:",ModeSelect)
        if ModeSelect == b'c':#模式选择：c-扫码传输颜色组
            GetCode()
            print(ColorCode1)
            print(ColorCode2)
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
        elif ModeSelect == b't': #模式选择：t-阈值显示器
            CameraStartup()
            ColorThresholds()
        elif ModeSelect == b'i': #模式选择：i-圆阈值显示器
            CameraStartupHD()
            CircleThresholds()
        elif ModeSelect == b'n': #模式选择：n-导航模式
            CameraStartupHD()
            Navigation()
        LED(2).off()
        LED(3).on()
