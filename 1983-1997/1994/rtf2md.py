import os
import pypandoc

# # 下载并安装 Pandoc（如果尚未安装）
# pypandoc.download_pandoc()

# 设置目标目录
target_dir = r'F:\data\1983-1997\1997'

# 切换到目标目录
os.chdir(target_dir)

# 获取目标目录下的所有文件
files = os.listdir('.')

# 遍历所有文件
for file in files:
    # 检查文件是否为 RTF 文件
    if file.endswith('.rtf'):
        # 生成对应的 TXT 文件名
        txt_file = file.replace('.rtf', '.txt')
        
        # 使用 pypandoc 将 RTF 文件转换为 TXT 文件
        pypandoc.convert_file(file, 'plain', outputfile=txt_file)
        
        print(f"已将 {file} 转换为 {txt_file}")

print("所有 RTF 文件已转换为 TXT 文件。")