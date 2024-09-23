import sensor, image, time, math, pyb
from pyb import UART

#初始化一阶段，色块识别
sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # grayscale is faster
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time = 2000)
sensor.set_windowing((320, 240))
BlobLocation=[0,0,0]
roi_blob=(159,119,1,1)# 设置ROI区域为画面正中心的1像素
roi_circle=(130,90,60,60)
state = 0
#阈值选择器
L_red = (38, 62, 21, 81, -31, 47)
L_green = (21, 36, -48, -6, -32, 37)
LocationThreshold=[[L_red], [L_green]]
#初始化UART
uart = UART(3, 115200)
# 其他参数
pixels_threshold = 1
area_threshold = 1
# 矫正阈值
ABSLoc = 5

while True:
    while state != 2:#找红色色块
        BlobLocation=[0,0,0]
        img = sensor.snapshot().lens_corr(1.8)
        for i in range(2):
            BlobLocation[i] = img.find_blobs(LocationThreshold[i], merge=True, roi = roi_blob)
            img.draw_rectangle(roi_blob)
            print(BlobLocation)
        if BlobLocation[0]:
            uart.write(str('R'))
            print("Get Red")
            state = 1
        if state == 1:
            if BlobLocation[1]:
                uart.write(str('G'))
                print("Get Green")
                state = 2

    while True:
        img = sensor.snapshot().lens_corr(1.8)
        for c in img.find_circles(
        threshold=500,
        x_margin=20,
        y_margin=20,
        r_margin=30,
        r_min=2,
        r_max=200,
        r_step=2,
        roi=roi_circle
        ):
            img.draw_circle(c.x(), c.y(), c.r(), color=(255, 0, 0))
            img.draw_cross(c.x(), c.y(), color=(255, 0, 0))
            if c.r() < 10:
                uart.write(str('C'))
                if c.x()-160 > ABSLoc:
                    uart.write(str('A'))
                if c.x()-160 < -ABSLoc:
                    uart.write(str('D'))
                if c.y()-120 > ABSLoc:
                    uart.write(str('W'))
                if c.y()-120 < -ABSLoc:
                    uart.write(str('S'))
                print("Get Circle")
                ##print(c)















