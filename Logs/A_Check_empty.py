import os


all_files = os.listdir("./Logs/")
print(all_files)
tickers = filter(lambda x: x[-4:] == '.txt', all_files)


for t in tickers:
    if os.stat(f"./Logs/{t}").st_size == 0:
        print(f"{t}.txt is leeg en wordt verwijderd.")
        os.remove(f"./Logs/{t}")
    else:
        print(f"{t}.txt is niet leeg.")