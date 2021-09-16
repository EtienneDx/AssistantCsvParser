import csv
import datetime
data = []
classes = []
labels = []
with open("matieres.txt") as matieres:
    for line in matieres:
        if not line.startswith("#"):
            classes.append(line.rstrip())
with open('liste_cours_dec.csv') as csvfile:
    csvreader = csv.DictReader(csvfile, delimiter=';')
    i = 0
    for row in csvreader:
        if i == 0:
            labels = list(row.keys())
        if i % 1000 == 0:
            print(i)
        i = i + 1
        if "ECE PARIS ING" in row["NOM_DIP"] and (row["TYPE"] == "COURS-TD-OL" or row["TYPE"] == "COURS-TP-OL"):
            b = False
            for c in classes:
                if c in row["LIBELLE_MAT"]:
                    # row["LIBELLE_MAT"] = c
                    b = True
            if b:
                data.append(row)

print("pre-sorted " + str(len(data)) + " lines")
with open("out.csv", "w", newline='') as newcsv:
    writer = csv.writer(newcsv)
    writer.writerow(["MAT", "GRP", "PROF", "DATE", "HDEBUT", "HFIN"])
    for row in data:
        writer.writerow([row["LIBELLE_MAT"], row["NOM_DIP"][-11:], row["NOM_ENS"], row["DDEBUT"], row["HDEBUT"], row["HFIN"]])
