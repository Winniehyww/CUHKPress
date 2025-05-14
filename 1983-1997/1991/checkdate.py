import os
import re
import pandas as pd

def extract_dates_from_excel(excel_file):
    """从 Excel 文件中提取日期及其上下文信息"""
    try:
        # 读取 Excel 文件
        df = pd.read_excel(excel_file)
        
        date_counts = {}
        date_contexts = {}
        
        # 假设 Excel 中有日期列，具体列名需要根据实际文件调整
        # 尝试查找包含日期的列
        date_column = None
        for col in df.columns:
            if 'date' in col.lower() or '日期' in col:
                date_column = col
                break
        
        if not date_column:
            print("无法找到日期列，请检查 Excel 文件格式")
            return {}, {}
        
        # 处理每一行数据
        for index, row in df.iterrows():
            date_str = str(row[date_column])
            
            # 尝试提取日期 (YYYY-MM-DD)
            date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', date_str)
            
            # 如果没有找到标准格式，尝试其他可能的格式
            if not date_matches:
                # 尝试 YYYY/MM/DD 格式
                slash_matches = re.findall(r'(\d{4}/\d{2}/\d{2})', date_str)
                if slash_matches:
                    date_matches = [match.replace('/', '-') for match in slash_matches]
                else:
                    # 尝试 YYYYMMDD 格式
                    compact_matches = re.findall(r'(\d{8})', date_str)
                    if compact_matches:
                        date_matches = [f"{match[:4]}-{match[4:6]}-{match[6:8]}" for match in compact_matches]
            
            # 处理找到的日期
            for date in date_matches:
                if date in date_counts:
                    date_counts[date] += 1
                else:
                    date_counts[date] = 1
                
                # 存储该行的所有信息作为上下文
                row_context = [f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])]
                
                if date in date_contexts:
                    date_contexts[date].append(row_context)
                else:
                    date_contexts[date] = [row_context]
        
        return date_counts, date_contexts
    
    except Exception as e:
        print(f"处理 Excel 文件时出错: {e}")
        return {}, {}

def extract_dates_from_pdf_filenames(pdf_dir):
    """从 PDF 文件名中提取日期，同时记录文件后缀"""
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    date_counts = {}
    date_files = {}  # 新增字典，记录每个日期对应的文件名
    
    for filename in pdf_files:
        # 从文件名中提取日期，格式如 cuhkpr-19910320e.pdf
        match = re.search(r'(\d{4})(\d{2})(\d{2})([a-zA-Z])?', filename)
        if match:
            year, month, day, suffix = match.groups()
            suffix = suffix or ""  # 如果没有后缀，设为空字符串
            date = f"{year}-{month}-{day}"
            
            if date in date_counts:
                date_counts[date] += 1
                date_files[date].append(f"{filename}")
            else:
                date_counts[date] = 1
                date_files[date] = [f"{filename}"]
    
    return date_counts, date_files

def compare_dates(excel_dates, pdf_dates, pdf_files):
    """比较 Excel 和 PDF 文件中的日期"""
    all_dates = set(list(excel_dates.keys()) + list(pdf_dates.keys()))
    
    results = []
    for date in sorted(all_dates):
        excel_count = excel_dates.get(date, 0)
        pdf_count = pdf_dates.get(date, 0)
        
        if excel_count > pdf_count:
            results.append({
                "date": date,
                "status": "missing",
                "diff": excel_count - pdf_count,
                "files": pdf_files.get(date, [])
            })
        elif excel_count < pdf_count:
            results.append({
                "date": date,
                "status": "redundant",
                "diff": pdf_count - excel_count,
                "files": pdf_files.get(date, [])
            })
    
    return results

def main():
    # 设置文件路径
    excel_file = f"F:/data/1983-1997/1984/1984articles.xlsx"
    pdf_dir = f"F:/data/1983-1997/1984"
    
    # 从 Excel 和 PDF 文件中提取日期
    excel_dates, date_contexts = extract_dates_from_excel(excel_file)
    pdf_dates, pdf_files = extract_dates_from_pdf_filenames(pdf_dir)
    
    # 比较日期
    results = compare_dates(excel_dates, pdf_dates, pdf_files)
    
    # 输出结果
    if results:
        print("\n不匹配的日期:")
        for result in results:
            print(f"{result['date']}: {result['status']} ({result['diff']})")
            if result['files']:
                print(f"  现有文件: {', '.join(result['files'])}")
    else:
        print("\n所有日期都匹配!")
    
    # 打印统计信息
    print(f"\nExcel 文件中的日期数量: {sum(excel_dates.values())}")
    print(f"PDF 文件数量: {sum(pdf_dates.values())}")
    
    # 打印所有不匹配日期的详细信息
    if results:
        print("\n不匹配日期的详细信息:")
        for result in results:
            date = result['date']
            print(f"\n{date} ({result['status']}, 差异: {result['diff']}):")
            
            # 打印 Excel 中的信息
            if date in excel_dates:
                print(f"  在 Excel 中出现 {excel_dates[date]} 次")
            else:
                print(f"  {date} 在 Excel 中未找到")
            
            # 打印 PDF 文件信息
            if date in pdf_dates:
                print(f"  有 {pdf_dates[date]} 个 PDF 文件:")
                for file in pdf_files[date]:
                    print(f"    {file}")
            else:
                print(f"  {date} 没有对应的 PDF 文件")

if __name__ == "__main__":
    main()