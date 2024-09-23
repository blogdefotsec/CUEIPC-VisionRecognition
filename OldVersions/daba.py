import sensor, image, time, math,pyb
from pyb import UART

blue = (0, 47, -128, 31, -128, -13)
red =  (0, 56, 18, 127, -18, 127)
green = (25, 80, -128, -17, -128, 127)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()
while (True):
    # if(y_err==100):
    # print("前后")
    x0 = 100
    y0 = 100
    clock.tick()
    img = sensor.snapshot().lens_corr(2.0).gamma_corr(gamma=1.5, contrast=1.3, brightness=0.0)
    for c in img.find_circles(threshold=3000, x_margin=20, y_margin=20, r_margin=30,
                              r_min=2, r_max=200, r_step=2):
        area_1 = (c.x() - c.r(), c.y() - c.r(), 2 * c.r(), 2 * c.r())
        img.draw_rectangle(area_1, color=(0, 255, 255))
        for blob in img.find_blobs([white_threshold], x_stride=10, y_stride=10, roi=area_1, ):
            if blob.density() > 0.7 and blob.area() > 1200:
                img.draw_rectangle(blob[0:4])
                y_err = blob[6] - x0  # 小于60向后 大于60向前
                x_err = blob[5] - y0
                if (uart.any()):
                    flag = uart.read()
                    if (flag == b'd'):
                        # print("收到d")
                        if (abs(y_err) > 1):
                            if (y_err > 0):
                                uart.write('1')
                                y_err = 100
                                # print("发送1")
                            if (y_err < 0):
                                uart.write('2')
                                y_err = 100
                                # print("发送2")
                        else:
                            uart.write('3')
                            # print("发送3")
                            flag = 'z'
                            y_err = 100
                            break