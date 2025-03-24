import os
import argparse
import re
import csv
import cadquery as cq

def create_cylinder_step(output_filename, H1, H2, H3, D1, D2, D3, D4, _):
    """
    指定されたパラメータで3Dモデル（STEPファイル）を生成する関数
    """
    # 下側フランジの作成
    model = (
        cq.Workplane("XY").circle(D2 / 2).circle(D4 / 2).extrude(H1)
    )

    # 筒部分の作成
    model = (
        model.faces(">Z").workplane().circle(D3 / 2).circle(D4 / 2).extrude(H2)
    )

    # 上側フランジの作成
    model = (
        model.faces(">Z").workplane().circle(D1 / 2).circle(D4 / 2).extrude(H3)
    )

    # 上端フランジの外周エッジにフィレット適用
    model = model.edges(cq.selectors.NearestToPointSelector((0, 0, H2 + H3 + H1 ))).fillet(H3 / 2)

    # 下端フランジの外周エッジにフィレット適用
    model = model.edges(cq.selectors.NearestToPointSelector((0, 0, 0))).fillet(H1 / 2)

    # STEPファイルとして一時保存
    step_filename = f"{output_filename}.step"
    cq.exporters.export(model, step_filename)

    print(f"STEPファイルを生成しました: {step_filename}")

def merge_step(csv_data, output_filename):
    """
    複数のSTEPファイルをインポートし、X軸の指定位置に配置して統合し、1つのSTEPファイルに保存する関数
    :param csv_data: 生成データリスト
    :param output_filename: 統合後のSTEPファイル名
    """
    merged_model = None  # 最初は空のモデル

    for row in csv_data:
        step_file = row[0]+".step"  # インポートするSTEPファイル名
        x_position = float(row[8])  # X座標の指定位置
        
        try:
            # STEPファイルをインポート
            part = cq.importers.importStep(step_file)

            # 指定されたX座標に移動
            part = part.translate((x_position, 0, 0))

            # 既存のモデルに統合
            if merged_model is None:
                merged_model = part
            else:
                merged_model = merged_model.union(part)

            print(f"インポート: {step_file} を X={x_position} に配置")

            # インポートしたstepファイルを削除
            os.remove(step_file)

        except Exception as e:
            print(f"エラー: {step_file} のインポートに失敗 - {e}")

    # STEPファイルとして保存
    if merged_model:
        cq.exporters.export(merged_model, output_filename)
        print(f"統合STEPファイルを生成しました: {output_filename}")
    
    # リネーム
    with open(output_filename, "r", encoding="utf-8") as f:
        strAllData = f.read()
    count = len(csv_data)+1
    print(count)
    for idx, row in enumerate(csv_data):
        src_name = f"'Open CASCADE STEP translator 7.7 {count}.{idx+1}'"
        dst_name =f"'{row[0]}'"
        strAllData = strAllData.replace(src_name, dst_name)

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(strAllData)

def read_csv(csv_file, skipHeader = True):
    # CSVを読み込んでリストに格納
    retVal = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        if skipHeader:
            header = next(reader)  # ヘッダーをスキップ        
        for row in reader:
            retVal.append(row)

    return retVal

def main():
    """
    主処理
    """

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="円筒形オブジェクトの自動作図")
    parser.add_argument("csv_file", help="入力CSVファイル名", default="input_data.csv", nargs="?")
    parser.add_argument("output_step", help="出力STEPファイル名", default="output.step", nargs="?")
    args = parser.parse_args()

    csv_data = read_csv(args.csv_file)

    for row in csv_data:
        # 各パラメータを取得
        output_filename = row[0]  # 出力するSTEPファイル名
        params = [float(value) for value in row[1:]]  # 数値パラメータを変換

        # STEPファイルを生成
        create_cylinder_step(output_filename, *params)

    print("マージ")
    merge_step(csv_data, args.output_step)

if __name__ == "__main__":
    main()
