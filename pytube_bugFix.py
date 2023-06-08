#pytubeのエラーがでたらこのファイルを実行してください
import os
import sys
import glob

path = os.path.dirname(sys.executable)
target = f"{path}\Lib\site-packages\pytube\cipher.py"
if os.path.exists(target) == False:
    print("pytubeが正常にインストールされていません")
else:
    with open(target,"r",encoding="utf-8") as f:
        text = f.read()
        old = 'var_regex = re.compile(r"^\w+\W")'
        new = 'var_regex = re.compile(r"^\$*\w+\W")'
        newText = text.replace(old,new)
    with open(target,"w",encoding="utf-8") as f:
        f.write(newText)
    print("完了しました")
input()