"""
从 Excel 导入名单到数据库

用法：
    python scripts/import_excel.py /path/to/名单.xlsx
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import create_app, db
from app.models import Person


def import_from_excel(filepath):
    """从 Excel 文件导入人员名单"""
    df = pd.read_excel(filepath, header=None)

    # 查找包含 "姓名" 和 "学号" 的标题行
    header_row = None
    name_col = None
    student_id_col = None

    for row_idx in range(min(10, len(df))):
        for col_idx in range(len(df.columns)):
            cell = str(df.iloc[row_idx, col_idx]).strip()
            if '姓名' == cell or cell.startswith('姓名'):
                name_col = col_idx
                header_row = row_idx
            if '学号' == cell or cell.startswith('学号'):
                student_id_col = col_idx
                header_row = row_idx

    if name_col is None or student_id_col is None:
        print('❌ 未找到"姓名"或"学号"列')
        print(f'  找到的列: name_col={name_col}, student_id_col={student_id_col}')
        return

    print(f'✅ 找到表头行 {header_row}，姓名列 {name_col}，学号列 {student_id_col}')

    app = create_app()
    with app.app_context():
        added = 0
        skipped = 0
        errors = []

        for row_idx in range(header_row + 1, len(df)):
            name = str(df.iloc[row_idx, name_col]).strip()
            student_id = str(df.iloc[row_idx, student_id_col]).strip()

            # 跳过空行和非数字学号（排除标题/合并单元格残留）
            if not name or name == 'nan':
                continue
            if not student_id or student_id == 'nan':
                continue
            if not student_id.isdigit():
                continue

            # 检查是否已存在（按姓名或学号）
            existing = Person.query.filter(
                (Person.name == name) | (Person.student_id == student_id)
            ).first()
            if existing:
                errors.append(f'跳过: {name} ({student_id}) - 已存在')
                skipped += 1
                continue

            person = Person(name=name, student_id=student_id, department='电气工程学院')
            db.session.add(person)
            added += 1

        db.session.commit()

        print(f'\n📊 导入完成:')
        print(f'  新增: {added} 人')
        print(f'  跳过: {skipped} 人')
        if errors:
            print(f'  详情:')
            for e in errors[:10]:
                print(f'    {e}')

        # 验证
        total = Person.query.count()
        print(f'  数据库总人数: {total}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python scripts/import_excel.py <Excel文件路径>')
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f'❌ 文件不存在: {filepath}')
        sys.exit(1)

    import_from_excel(filepath)
