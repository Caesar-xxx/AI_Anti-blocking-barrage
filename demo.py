# -*- coding:utf-8 -*-
"""
作者：知行合一
日期：2019年 06月 16日 11:22
文件名：demo1.py
地点：changsha
"""

# 导入相关包
import cv2
import numpy as np
import pixellib

# 导入实例分割
from pixellib.instance import instance_segmentation

# 导入弹幕管理模块
from danmu import Danmu_layer

import os
from PIL import Image

# 视频文件每帧画面转为蒙版图片存储
class VideoProcess:

    def __init__(self,videoFile):
        """
        构造方法
        @param videoFile mp4格式视频
        """
        self.videoFile = videoFile


    def video2masks(self):
        """
        视频文件转为MASKS 图片


        """
        # 实例分割实例化
        instance = instance_segmentation()

        # 加载模型
        instance.load_model('./weights/mask_rcnn_coco.h5')

        # 筛选类别
        target_classes = instance.select_target_classes(person=True)

        # 读取视频
        cap = cv2.VideoCapture(self.videoFile)

        # 记录帧数
        frame_index = 0


        while True:
            # 读取视频
            ret,frame = cap.read()

            # 判断是否视频是否处理完
            if not ret:
                print('视频处理完毕')
                break

            # 实例分割
            results, output = instance.segmentFrame(frame, segment_target_classes=target_classes)

            # 人数
            person_count = len(results['class_ids'])

            # 判断人数
            if person_count > 0:
                # 遮罩
                mask = results['masks']

                # 创建黑色底图
                black_bg = np.zeros(frame.shape[:2])

                for p_index in range(person_count):
                     black_bg = np.where(mask[:,:,p_index]==True,255,black_bg)

                # 文件名
                mask_file = './masks_img/' + str(frame_index) + '.jpg'
                cv2.imwrite(mask_file,black_bg)

                print('第%d帧处理完毕' % (frame_index))

            else:
                print('第%d帧无人' % (frame_index))

            frame_index += 1

        #     # 显示渲染图
        #     cv2.imshow('Picture',output)
        #
        #     # 退出条件
        #     if cv2.waitKey(10) & 0xFF == ord('q'):
        #
        #         break
        #
        # cap.release()
        # cv2.destroyAllWindows()



    def video_composite(self):
        """
        合成弹幕视频
        1、读取视频第X帧画面
        2、获取第X帧弹幕层画面，并用蒙版处理
        3、合成弹幕层与视频层
        4、保存为视频文件
        """

        # 读取视频
        cap = cv2.VideoCapture(self.videoFile)

        # 获取视频宽度和高度
        frame_w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 获取帧率
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # 弹幕层实例化
        text_path = 'danmu_real.txt'
        danmu_layer = Danmu_layer(text_path, frame_w, frame_h)

        # 构建视频写入器
        video_name = './out_video/output.mp4'
        video_writer = cv2.VideoWriter(video_name,cv2.VideoWriter_fourcc(*'MP4V'),fps,(frame_w,frame_h))

        # 记录帧数
        frame_index = 0
        while True:
            # 读取视频
            ret, frame = cap.read()

            # 判断是否视频是否处理完
            if not ret:
                print('视频处理完毕')
                break
            # 获取弹幕层
            frame_danmu_layer = danmu_layer.generate_frame(frame_index)

            # 对弹幕层进行蒙版操作
            # 蒙版文件
            mask_file = './masks_img/' + str(frame_index) + '.jpg'

            # 判断蒙版文件是否存在
            if os.path.exists(mask_file):
                mask_img = cv2.imread(mask_file)
                # 转为灰度图
                mask_gray = cv2.cvtColor(mask_img,cv2.COLOR_BGR2GRAY)

                # 对弹幕层进行处理
                # 弹幕层转为numpy数组
                frame_danmu_layer_np = np.array(frame_danmu_layer)

                # 对弹幕层alpha通道进行处理
                frame_danmu_layer_np[:,:,3] = np.where(mask_gray==255,0,frame_danmu_layer_np[:,:,3])

                # 转为RGBA
                frame_danmu_layer = Image.fromarray(frame_danmu_layer_np)

            # 合成弹幕层与视频层
            # 转为RGBA的Image格式
            frame_rgba = cv2.cvtColor(frame,cv2.COLOR_BGR2RGBA)

            frame_rgba_pil = Image.fromarray(frame_rgba)

            output = Image.alpha_composite(frame_rgba_pil,frame_danmu_layer)

            # 转为numpy数组
            output_np = np.asarray(output)

            # 转为BGR
            output = cv2.cvtColor(output_np,cv2.COLOR_RGBA2BGR)

            video_writer.write(output)
            # 显示渲染图
            cv2.imshow('Picture', output)

            frame_index += 1

            # 退出条件
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        video_writer.release()
        cap.release()
        cv2.destroyAllWindows()


# 实例化
vp = VideoProcess('./videos/video.mp4')
# vp.video2masks()
vp.video_composite()