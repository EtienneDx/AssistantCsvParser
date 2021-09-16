import csv
import datetime
import os
import re
import argparse

parser = argparse.ArgumentParser(description="Ce script sert a générer les fichiers csv permettant le suivi des assistants")
parser.add_argument("-c", "--clean", dest="clean", action="store_true", help="Vide le répértoire de sortie avant de générer les fichiers")
parser.add_argument("-d", "--discord", dest="discord", action="store_true", help="Exporte un fichier au format du bot discord")
parser.add_argument("-m", "--matieres", dest="matieres", action="store", default="matieres.txt", help="Fichier listant les matières (par défaut, matieres.txt)")
parser.add_argument("-p", "--planning", dest="planning", action="store", default="planning.csv", help="Fichier listant les cours (par défaut, planning.csv)")

args = parser.parse_args()

out_folder = "out"

if args.clean:
    for filename in os.listdir(out_folder):
        file_path = os.path.join(out_folder, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

data = []
classes = []
labels = []
# on liste les matieres
with open(args.matieres) as matieres:
    for line in matieres:
        if not line.startswith("#"):# commentairs autorisés
            m = line.rstrip()
            presOnly = len(m.split(";")) > 1 and m.split(";")[1] == "P"
            m = m.split(";")[0]
            classes.append([m, re.compile(m), presOnly])# on les compile en regex pour les accents qui foutent le bazar
with open(args.planning) as csvfile:
    csvreader = csv.DictReader(csvfile, delimiter=';')# lecture du fichier
    i = 0
    for row in csvreader:# chaque ligne
        if i == 0:
            labels = list(row.keys())# recup des labels
        if i % 1000 == 0:
            print(i)# affichage progression
        i = i + 1

        # Cours de l'ECE et du type voulu
        if "ECE PARIS ING" in row["NOM_DIP"] and (row["TYPE"] == "COURS-TD-OL" or row["TYPE"] == "COURS-TP-OL" or row["TYPE"] == "COURS-TD" or row["TYPE"] == "COURS-TP"):
            b = False
            # marqueur pour identifier les cours en ligne
            online = row["TYPE"] == "COURS-TD-OL" or row["TYPE"] == "COURS-TP-OL"
            for c in classes:
                # si c'est un des cours voulu
                if c[1].match(row["LIBELLE_MAT"]) and not (c[2] and online) and not (args.discord and not online):
                    if not args.discord:
                        row["LIBELLE_MAT"] = c[0]
                    if row["TYPE"] == "COURS-TD-OL" or row["TYPE"] == "COURS-TP-OL":
                        row["NOM_SAL"] = "discord"
                    elif row["NOM_SAL"] == "":
                        row["NOM_SAL"] = "Présentiel"
                    b = True
            if b:
                data.append(row)
print("pre-sorted " + str(len(data)) + " lines")

if args.discord:
    with open(out_folder + "/discord.csv", "w", newline='') as newcsv:
        writer = csv.writer(newcsv)
        writer.writerow(["MAT", "GRP", "PROF", "DATE", "HDEBUT", "HFIN"])
        for row in data:
            writer.writerow([row["LIBELLE_MAT"], row["NOM_DIP"][-11:], row["NOM_ENS"], row["DDEBUT"], row["HDEBUT"], row["HFIN"]])
else:
    resalle = re.compile(r"([a-zA-Z0-9]+ [^-<>]+- [^ \(]+)")

    # Creation du tableau pour rassembler les cours d'une meme matiere
    lib_mat = {}
    for row in data:
        if not row["LIBELLE_MAT"] in lib_mat:
            lib_mat[row["LIBELLE_MAT"]] = {}
        grp_nom = row["NOM_DIP"][-9:]
        if not grp_nom in lib_mat[row["LIBELLE_MAT"]]:
            lib_mat[row["LIBELLE_MAT"]][grp_nom] = {
                "ENSEIGNANT": row["NOM_ENS"],
                "COURS": []
            }

        salle = row["NOM_SAL"]
        g = resalle.finditer(salle)
        ns = ""
        for m in g:
            ns = ns + (", " if ns != "" else "") + m[1]
        if ns != "":
            salle = ns


        lib_mat[row["LIBELLE_MAT"]][grp_nom]["COURS"].append({
            "DATE": row["JOUR"] + " " + row["DDEBUT"][0:5],
            "WEEK": datetime.datetime.strptime((row["DDEBUT"]), "%d/%m/%Y").isocalendar()[1],
            "HEURE": row["HDEBUT"] + " - " + row["HFIN"],
            "SALLE": salle
        })

    # utilité de tri
    def sort_week(elem):
        return elem["WEEK"]

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    # tri
    for lib, mat in lib_mat.items():
        for td, dat in mat.items():
            dat["COURS"].sort(key=sort_week)

        out_data = [[lib, ""]]

        # on tri les tds
        for td in sorted(mat.keys()):
            out_data.append([td + "\n" + mat[td]["ENSEIGNANT"], "Jour"])
            out_data.append(["", "Horaire"])
            out_data.append(["", "Salle"])
            out_data.append(["", "Assistant"])

        done = False
        while not done:
            done = True
            nextWeek = 100
            for td in sorted(mat.keys()):
                if len(mat[td]["COURS"]) > 0:
                    done = False
                    if mat[td]["COURS"][0]["WEEK"] < nextWeek:
                        nextWeek = mat[td]["COURS"][0]["WEEK"]

            # quelque chose a ajouter?
            if not done:
                out_data[0].append("Semaine " + str(nextWeek))
                i = 0
                for td in sorted(mat.keys()):
                    if len(mat[td]["COURS"]) > 0 and mat[td]["COURS"][0]["WEEK"] == nextWeek:
                        out_data[4*i + 1].append(mat[td]["COURS"][0]["DATE"])
                        out_data[4*i + 2].append(mat[td]["COURS"][0]["HEURE"])
                        out_data[4*i + 3].append(mat[td]["COURS"][0]["SALLE"])
                        out_data[4*i + 4].append("")
                        mat[td]["COURS"].pop(0)
                    else:
                        out_data[4*i + 1].append("")
                        out_data[4*i + 2].append("")
                        out_data[4*i + 3].append("")
                        out_data[4*i + 4].append("")
                    i += 1
        
        # on ecrit le resultat final
        with open(out_folder + "/" + lib + ".csv", "w", newline='') as export:
            writer = csv.writer(export, delimiter=';')
            writer.writerows(out_data)
