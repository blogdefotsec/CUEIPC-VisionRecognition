import sensor, image, time, math, pyb
from pyb import UART

# 颜色阈值
red = (26, 43, 35, 82, -26, 57)
green = (21, 36, -48, -6, -32, 37)
blue = (16, 43, 17, 64, -101, -54)

# 其他参数
pixels_threshold = 100
area_threshold = 100
thresholds = [[red], [green], [blue]] #0-红色，1-绿色，2-蓝色

# 初始化坐标
middle_threshold = 100 #没用过的变量
flag = b"q"
biao = b"q"
FLAG = 0
group_1x = [0 for x in range(3)]
group_1y = [0 for x in range(3)]
code_1 = [0 for x in range(3)]  
code_2 = [0 for x in range(3)]
newx = [0, 0, 0]
jishu = 0
jishu_1 = 0
state_1 = 0

# 初始化串口
uart = UART(3, 115200)

#对应的是arduino中的chuanshu模块，接收到二维码扫到的2组共6个颜色
def Get_Code():
    global FLAG, a
    a = 0  
    while FLAG != 6:  
        FLAG = 0  
        if uart.any():  
            a = uart.read()  
            a = str(a)  
            for i in range(0, 3):  
                code_1[i] = int(a[2+i])  
                FLAG += 1  
                print(code_1[i])  
            for i in range(0, 3):  
                code_2[i] = int(a[5+i])  
                FLAG += 1  
                print(code_2[i])  

# 寻找停止状态
def find_stopstate():
    # 如果检测到颜色块，证明当前有物块在视野内。进入停止状态。
    global blobs, state, yanse
    blobs = 0
    state = 0
    yanse = [0, 0, 0]
    group_oldx = [999 for x in range(3)]
    img = sensor.snapshot().lens_corr(1.5)
    for i in range(3):# 0-红色 1-绿色 2-蓝色。循环三次，读取三个颜色的位置。
        blobs = img.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)#根据阈值寻找色块位置
        if blobs:
            for b in blobs:
                img.draw_rectangle(b.rect())#画框
                img.draw_cross(b.cx(), b.cy())#画中心点
                group_oldx[i] = b.cx()
                group_oldy[i] = b.cy()
                yanse[i] = i + 1#下一个颜色的序号
        else:
            group_oldx[i] = 0
            group_oldy[i] = 0
    while state == 0:
        get_new()
        if (group_oldx[1] == 0 and group_oldx[2] == 0 and group_oldx[0] == 0 and group_newx[1] == 0 and group_newx[2] == 0 and group_newx[0] == 0):
            state = 0
        elif (abs(group_oldx[1] - group_newx[1]) < 2 and abs(group_oldx[2] - group_newx[2]) < 2 and abs(group_oldx[0] - group_newx[0]) < 2):
            while state_1 == 0:
                get_new_color()
                if (yanse[1] - yanse_new[1] == 0 and yanse[2] - yanse_new[2] == 0 and yanse[0] - yanse_new[0] == 0):
                    yanse = yanse_new
                else:
                    state_1 = 1
                    print(yanse_new)
                    print(yanse)
                    print('jieshou')
                    find_stop()
            state = 1
        else:
            group_oldx = group_newx
            group_oldy = group_newy
            pass

# 获取新物料位置
def get_new_color():
    global yanse_new
    yanse_new = [0 for x in range(3)]
    img1 = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        blobs = img1.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if blobs:
            for b in blobs:
                yanse_new[i] = i + 1
        else:
            pass

def get_new():
    global group_newx, group_newy
    group_newx = [0 for x in range(3)]
    group_newy = [0 for x in range(3)]
    sensor.skip_frames(time=500)
    img1 = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        blobs = img1.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if blobs:
            for b in blobs:
                img1.draw_rectangle(b.rect())
                img1.draw_cross(b.cx(), b.cy())
                group_newx[i] = b.cx()
        else:
            pass

def xunzhao_wuliao():
    global jishu, xunzhao, chongxing, blobs
    xunzhao = [0, 0, 0]
    k = 0
    chongxing = 1
    blobs = 0
    img1 = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        blobs = img1.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if blobs:
            for b in blobs:
                img1.draw_rectangle(b.rect())
                img1.draw_cross(b.cx(), b.cy())
                newx[i] = b.cx()
                xunzhao[i] = i + 1
                print(xunzhao)
        else:
            pass
    for k in range(3):
        if xunzhao[k] == code_1[jishu]:
            if k == 0:
                uart.write(str('R'))
                jishu += 1
                print('R')
                time.sleep(5.5)
                break
            if k == 1:
                uart.write(str('G'))
                jishu += 1
                print('G')
                time.sleep(5.5)
                break
            if k == 2:
                uart.write(str('B'))
                jishu += 1
                print('B')
                time.sleep(5.5)
                break
        else:
            pass

def xunzhao_wuliao_1():
    global jishu_1, xunzhao, chongxing, blobs
    xunzhao = [0, 0, 0]
    k = 0
    chongxing = 1
    blobs = 0
    img1 = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        blobs = img1.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if blobs:
            for b in blobs:
                img1.draw_rectangle(b.rect())
                img1.draw_cross(b.cx(), b.cy())
                newx[i] = b.cx()
                xunzhao[i] = i + 1
                print(newx)
                print(xunzhao)
        else:
            pass
    for k in range(3):
        if xunzhao[k] == code_2[jishu_1]:
            if k == 0:
                uart.write(str('R'))
                jishu_1 += 1
                print('R')
                time.sleep(5.5)
                break
            if k == 1:
                uart.write(str('G'))
                jishu_1 += 1
                print('G')
                time.sleep(5.5)
                break
            if k == 2:
                uart.write(str('B'))
                jishu_1 += 1
                print('B')
                time.sleep(5.5)
                break

def find_stop():
    global blobs, state_2, group_oldx_1
    blobs = 0
    state_2 = 0
    group_oldx_1 = [999 for x in range(3)]
    img = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        blobs = img.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if blobs:
            for b in blobs:
                img.draw_cross(b.cx(), b.cy())
                group_oldx_1[i] = b.cx()
        else:
            group_oldx_1[i] = 0
    while state_2 == 0:
        get_new_1()
        if (group_oldx_1[1] == 0 and group_oldx_1[2] == 0 and group_oldx_1[0] == 0 and group_newx[1] == 0 and group_newx[2] == 0 and group_newx[0] == 0):
            state_2 = 0
        elif (abs(group_oldx_1[1] - group_newx_1[1]) < 1 and abs(group_oldx_1[2] - group_newx_1[2]) < 1 and abs(group_oldx_1[0] - group_newx_1[0]) < 1):
            state_2 = 1
        else:
            group_oldx_1 = group_newx_1
            pass

def get_new_1():
    global group_newx_1
    group_newx_1 = [0 for x in range(3)]
    sensor.skip_frames(time=500)
    img1 = sensor.snapshot().lens_corr(1.5)
    for i in range(3):
        blobs = img1.find_blobs(thresholds[i], pixels_threshold=pixels_threshold, area_threshold=area_threshold, merge=True)
        if blobs:
            for b in blobs:
                img1.draw_rectangle(b.rect())
                img1.draw_cross(b.cx(), b.cy())
                group_newx_1[i] = b.cx()
        else:
            pass

while True:
    if uart.any():
        flag = uart.read()
        print(flag)
    while flag == b'c':
        Get_Code()
        break
    if flag == b's':
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(time=200)
        sensor.set_auto_whitebal(False)
        sensor.set_auto_gain(False)
        while jishu != 3:
            find_stopstate()
            xunzhao_wuliao()
        uart.write(str('j'))
        print('结')
        flag = b'e'
    while flag == b'b':
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(time=200)
        sensor.set_auto_whitebal(False)
        sensor.set_auto_gain(False)
        while jishu_1 != 3:
            find_stopstate()
            xunzhao_wuliao_1()
        uart.write(str('s'))
        print('束')
        flag = b'e'
