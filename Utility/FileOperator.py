#
import os
import shutil
import logging


class FileOperator(object):
    @staticmethod
    def move_file(file_name, source_path, destination_path):
        logger = logging.getLogger()
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        try:
            shutil.move(os.path.join(source_path, file_name), os.path.join(destination_path, file_name))
        except IOError as e:
            logger.error("当前文件'%s'移动失败：%s。" % (file_name, e))
        else:
            logger.info("当前文件'%s'处理完毕,文件移动至%s目录下。" % (file_name, destination_path))
