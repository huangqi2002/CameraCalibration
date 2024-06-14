import os
import re
import shutil

def main_01():
    # 指定PDF文件所在的文件夹路径
    pdf_folder = 'D:/workspace/study/study'

    # 获取文件夹中所有的PDF文件
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    # 遍历每个PDF文件
    for pdf_file in pdf_files:
        # 构建目标文件夹路径，使用PDF文件名（去除扩展名）作为文件夹名
        folder_name = os.path.splitext(pdf_file)[0]
        parts = folder_name.split("+")
        if len(parts) >= 2:
            folder_name = parts[1] + parts[0]
        folder_path = os.path.join(pdf_folder, folder_name)

        # 如果文件夹不存在，则创建它
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # 构建源PDF文件路径和目标PDF文件路径
        source_pdf_path = os.path.join(pdf_folder, pdf_file)
        target_pdf_path = os.path.join(folder_path, pdf_file)

        # 移动PDF文件到目标文件夹
        shutil.move(source_pdf_path, target_pdf_path)
        print(source_pdf_path)

def main():
    # 指定PDF文件所在的文件夹路径
    pdf_folder = 'D:/workspace/study/study_0'

    # 获取文件夹中所有的PDF文件
    pdf_files = [f for f in os.listdir(pdf_folder) if any(f.endswith(extension) for extension in ['.pdf', '.docx', '.zip', '.rar'])]

    # 遍历每个PDF文件
    for pdf_file in pdf_files:
        # 构建目标文件夹路径，使用PDF文件名（去除扩展名）作为文件夹名
        folder_name = os.path.splitext(pdf_file)[0]
        parts = folder_name.split("+|-|_|2")

        pattern = re.compile(r'[\u4e00-\u9fa5]+')
        result_1 = pattern.search(folder_name).group()
        print(result_1)

        pattern = re.compile(r'\d+')
        result_2 = pattern.search(folder_name).group()
        print(result_2)

        folder_path = os.path.join(pdf_folder, result_2 + result_1)

        # 构建源PDF文件路径和目标PDF文件路径
        source_pdf_path = os.path.join(pdf_folder, pdf_file)
        target_pdf_path = os.path.join(folder_path, pdf_file)

        # 如果文件夹不存在，则创建它
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # 移动PDF文件到目标文件夹
        shutil.move(source_pdf_path, target_pdf_path)
        print(target_pdf_path)




if __name__ == "__main__":
    main()